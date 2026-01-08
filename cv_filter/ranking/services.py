import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db.models import Prefetch
from django.contrib.auth import get_user_model

from accounts.models import (
    Candidate,
    CandidateStructuredData,
    CandidateSummary,
    RankingRun,
    CandidateScore,
    RankingRunStatus,
)
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
        created_by: Optional[User],
        criteria: Dict[str, Any],
        bias_config: Optional[Dict[str, Any]] = None,
        candidate_filters: Optional[Dict[str, Any]] = None,
        max_candidates: int = 2000,
    ) -> RankingRun:
        # Create run
        run = RankingRun.objects.create(
            organization=organization,
            created_by_user=created_by,
            criteria_json=_to_primitive(criteria),
            bias_config_json=_to_primitive(bias_config or {}),
            status=RankingRunStatus.RUNNING,
            model_name="weighted-v1",
        )

        # Fetch candidates within organization
        qs = Candidate.objects.filter(organization=organization)
        if candidate_filters and candidate_filters.get("status"):
            qs = qs.filter(status__in=candidate_filters["status"])  # type: ignore

        qs = qs.order_by("created_at")[:max_candidates]

        candidates_data: List[Dict[str, Any]] = []
        id_to_candidate: Dict[str, Candidate] = {}
        for cand in qs:
            data = self.mapper.build_candidate_data(cand)
            candidates_data.append(data)
            id_to_candidate[str(cand.id)] = cand

        # Execute ranking
        ranked = self.engine.rank_candidates(
            candidates=candidates_data,
            criteria=criteria,
            weights=(bias_config if bias_config else None),
        )

        # Persist scores
        for item in ranked:
            cand_obj = id_to_candidate.get(item["id"])  # type: ignore
            if not cand_obj:
                continue
            CandidateScore.objects.create(
                organization=organization,
                ranking_run=run,
                candidate=cand_obj,
                score=item["score"],
                rank=item["rank"],
                details_json=item.get("details", {}),
                explanation=item.get("explanation", ""),
            )

        # Mark run complete
        run.status = RankingRunStatus.COMPLETED
        from django.utils import timezone

        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at"])
        return run

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
