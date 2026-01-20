import logging
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Prefetch
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import (
    Candidate,
    CandidateStructuredData,
    CandidateSummary,
    RankingRun,
    CandidateScore,
    RankingRunStatus,
)
from accounts.logging_service import AuditLogService
from .bias_detector import BiasPatternDetector
from .scoring.weighted_aggregator import create_scoring_engine

logger = logging.getLogger(__name__)
User = get_user_model()


def _to_primitive(value: Any) -> Any:
    """
    Convert Decimals and other non-JSON-serializable values to primitives.
    Ensures JSONField accepts input coming from serializers using DecimalField.
    """
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: _to_primitive(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_primitive(v) for v in value]
    return value


class CandidateDataMapper:
    """
    Map database models to the `candidate_data` dict expected by the scoring engine.
    """

    def build_candidate_data(self, candidate: Candidate) -> Dict[str, Any]:
        # Try to pull structured data
        structured = (
            CandidateStructuredData.objects.filter(
                organization=candidate.organization,
                cv_parse__cv_file__candidate=candidate,
            )
            .order_by("-created_at")
            .first()
        )

        skills: List[str] = []
        experience_years: Optional[float] = None
        education_level: Optional[str] = None
        education_field: Optional[str] = None
        positions: List[Dict[str, Any]] = []

        if structured:
            sj = structured.structured_json or {}
            # skills
            top_skills_text = structured.top_skills or sj.get("top_skills")
            if isinstance(top_skills_text, str):
                skills = [s.strip() for s in top_skills_text.split(",") if s.strip()]
            elif isinstance(top_skills_text, list):
                skills = [str(s).strip() for s in top_skills_text]

            # experience
            experience_years = float(structured.experience_years) if structured.experience_years else sj.get("experience_years")
            positions = sj.get("positions", []) if isinstance(sj.get("positions"), list) else []

            # education (optional)
            education = sj.get("education", {})
            education_level = education.get("level")
            education_field = education.get("field")

        # Fallbacks from candidate basic fields
        full_name = f"{candidate.first_name} {candidate.last_name}".strip()

        candidate_data: Dict[str, Any] = {
            "id": str(candidate.id),
            "full_name": full_name,
            "skills": skills,
            "experience_years": experience_years or 0.0,
            "positions": positions,
            "education_level": education_level or "",
            "education_field": education_field or "",
        }

        return candidate_data


class RankingService:
    """Coordinate ranking run creation, execution, and persistence."""

    def __init__(self):
        self.engine = create_scoring_engine()
        self.mapper = CandidateDataMapper()

    def start_and_execute_run(
        self,
        *,
        organization,
        created_by: Any,  # User model instance
        criteria: Dict[str, Any],
        bias_config: Optional[Dict[str, Any]] = None,
        candidate_filters: Optional[Dict[str, Any]] = None,
        max_candidates: int = 2000,
    ) -> RankingRun:
        """
        Start and execute a ranking run with detailed audit logging.
        
        Logs:
        - Run start with criteria
        - Candidate loading
        - Individual scoring
        - Run completion with statistics
        - Any errors that occur
        """
        start_time = time.time()
        
        # Create run
        run = RankingRun.objects.create(
            organization=organization,
            created_by_user=created_by,
            criteria_json=_to_primitive(criteria),
            bias_config_json=_to_primitive(bias_config or {}),
            status=RankingRunStatus.RUNNING,
            model_name="weighted-v1",
            started_at=timezone.now(),
        )

        # Log run start
        AuditLogService.log(
            organization=organization,
            event_type='ranking.run.started',
            entity_type='ranking_run',
            entity_id=run.id,
            actor_user=created_by,
            description=f'Ranking run started with ID {run.id}',
            metadata={
                'run_id': str(run.id),
                'criteria': _to_primitive(criteria),
                'has_bias_config': bias_config is not None,
                'max_candidates': max_candidates,
            }
        )

        try:
            # Fetch candidates within organization
            qs = Candidate.objects.filter(organization=organization)
            if candidate_filters and candidate_filters.get("status"):
                qs = qs.filter(status__in=candidate_filters["status"])  # type: ignore

            qs = qs.order_by("created_at")[:max_candidates]
            
            # Log candidate loading
            candidate_count = qs.count()
            AuditLogService.debug(
                organization=organization,
                event_type='ranking.candidates.loaded',
                entity_type='ranking_run',
                entity_id=run.id,
                actor_user=created_by,
                description=f'Loaded {candidate_count} candidates for ranking',
                metadata={
                    'run_id': str(run.id),
                    'candidate_count': candidate_count,
                    'filters': candidate_filters or {},
                }
            )

            candidates_data: List[Dict[str, Any]] = []
            id_to_candidate: Dict[str, Candidate] = {}
            for cand in qs:
                data = self.mapper.build_candidate_data(cand)
                candidates_data.append(data)
                id_to_candidate[str(cand.id)] = cand

            # Execute ranking
            scoring_start = time.time()
            ranked = self.engine.rank_candidates(
                candidates=candidates_data,
                criteria=criteria,
                weights=(bias_config if bias_config else None),
            )
            scoring_duration = time.time() - scoring_start

            # Log scoring completion
            AuditLogService.debug(
                organization=organization,
                event_type='ranking.scoring.completed',
                entity_type='ranking_run',
                entity_id=run.id,
                actor_user=created_by,
                description=f'Scored {len(ranked)} candidates in {scoring_duration:.2f}s',
                metadata={
                    'run_id': str(run.id),
                    'scored_count': len(ranked),
                    'scoring_duration_seconds': round(scoring_duration, 2),
                }
            )

            # Persist scores
            scores_created = 0
            score_stats = {
                'min': None,
                'max': None,
                'avg': 0.0,
            }
            
            all_scores = []
            for item in ranked:
                cand_obj = id_to_candidate.get(item["id"])  # type: ignore
                if not cand_obj:
                    continue
                    
                score_value = item["score"]
                all_scores.append(score_value)
                
                CandidateScore.objects.create(
                    organization=organization,
                    ranking_run=run,
                    candidate=cand_obj,
                    score=score_value,
                    rank=item["rank"],
                    details_json=item.get("details", {}),
                    explanation=item.get("explanation", ""),
                )
                scores_created += 1
                
                # Log individual candidate scoring (VERBOSE level)
                AuditLogService.verbose(
                    organization=organization,
                    event_type='ranking.candidate.scored',
                    entity_type='candidate',
                    entity_id=cand_obj.id,
                    actor_user=created_by,
                    description=f'Candidate {cand_obj.first_name} {cand_obj.last_name} scored {score_value:.2f}',
                    metadata={
                        'run_id': str(run.id),
                        'candidate_id': str(cand_obj.id),
                        'score': float(score_value),
                        'rank': item["rank"],
                        'details': item.get("details", {}),
                    }
                )
            
            # Calculate statistics
            if all_scores:
                score_stats['min'] = float(min(all_scores))
                score_stats['max'] = float(max(all_scores))
                score_stats['avg'] = float(sum(all_scores) / len(all_scores))
            
            # Bias pattern detection
            bias_detector = BiasPatternDetector()
            bias_analysis = bias_detector.analyze_score_distribution(all_scores)
            
            # Log bias analysis if indicators detected
            if bias_analysis['has_bias_indicators']:
                AuditLogService.log(
                    organization=organization,
                    event_type='ranking.bias.detected',
                    entity_type='ranking_run',
                    entity_id=run.id,
                    actor_user=created_by,
                    description=f'Bias indicators detected in ranking run {run.id}',
                    metadata={
                        'run_id': str(run.id),
                        'bias_indicators': bias_analysis['alerts'],
                        'score_statistics': bias_analysis['score_statistics'],
                        'recommendations': bias_analysis['recommendations'],
                        'overall_assessment': bias_detector._get_overall_assessment(bias_analysis)
                    }
                )

            # Mark run complete
            run.status = RankingRunStatus.COMPLETED
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "completed_at"])
            
            total_duration = time.time() - start_time
            
            # Log run completion with statistics
            AuditLogService.log(
                organization=organization,
                event_type='ranking.run.completed',
                entity_type='ranking_run',
                entity_id=run.id,
                actor_user=created_by,
                description=f'Ranking run {run.id} completed successfully',
                metadata={
                    'run_id': str(run.id),
                    'status': run.status,
                    'candidates_evaluated': candidate_count,
                    'scores_created': scores_created,
                    'total_duration_seconds': round(total_duration, 2),
                    'scoring_duration_seconds': round(scoring_duration, 2),
                    'score_statistics': score_stats,
                    'started_at': run.started_at.isoformat() if run.started_at else None,
                    'completed_at': run.completed_at.isoformat() if run.completed_at else None,
                }
            )
            
            return run
            
        except Exception as e:
            # Mark run as failed
            run.status = RankingRunStatus.FAILED
            run.completed_at = timezone.now()
            run.save(update_fields=["status", "completed_at"])
            
            error_duration = time.time() - start_time
            
            # Log failure
            AuditLogService.log(
                organization=organization,
                event_type='ranking.run.failed',
                entity_type='ranking_run',
                entity_id=run.id,
                actor_user=created_by,
                description=f'Ranking run {run.id} failed: {str(e)}',
                metadata={
                    'run_id': str(run.id),
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'duration_before_failure_seconds': round(error_duration, 2),
                }
            )
            
            logger.exception(f"Ranking run {run.id} failed")
            raise

    def fetch_results(self, *, run: RankingRun) -> List[Dict[str, Any]]:
        scores = (
            CandidateScore.objects.filter(ranking_run=run, organization=run.organization)
            .select_related("candidate")
            .order_by("rank")
        )
        results: List[Dict[str, Any]] = []
        for s in scores:
            results.append(
                {
                    "candidate_id": str(s.candidate_id),
                    "candidate_name": f"{s.candidate.first_name} {s.candidate.last_name}",
                    "score": float(s.score),
                    "rank": s.rank or 0,
                    "explanation": s.explanation or "",
                    "details_json": s.details_json or {},
                }
            )
        return results
