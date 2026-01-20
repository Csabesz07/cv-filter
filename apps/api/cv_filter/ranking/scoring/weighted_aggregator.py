"""
Weighted scoring aggregator - combines component scores into final ranking.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import ScoringEngine, ScoringResult
from .skill_matcher import SkillMatcher
from .experience_scorer import ExperienceScorer
from .education_scorer import EducationScorer
from .explainer import ScoringExplainer

logger = logging.getLogger(__name__)


DEFAULT_WEIGHTS = {
    'skill_weight': 0.50,
    'experience_weight': 0.30,
    'education_weight': 0.20,
}


class WeightedScoringEngine(ScoringEngine):
    """
    Complete scoring engine that aggregates multiple components.
    Implements the main scoring algorithm for candidate ranking.
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        skill_matcher: Optional[SkillMatcher] = None,
        experience_scorer: Optional[ExperienceScorer] = None,
        education_scorer: Optional[EducationScorer] = None,
        explainer: Optional[ScoringExplainer] = None,
    ):
        """
        Initialize weighted scoring engine.

        Args:
            weights: Component weights (uses DEFAULT_WEIGHTS if None)
            skill_matcher: SkillMatcher instance (creates default if None)
            experience_scorer: ExperienceScorer instance (creates default if None)
            education_scorer: EducationScorer instance (creates default if None)
            explainer: ScoringExplainer instance (creates default if None)
        """
        self.weights = self._validate_weights(weights or DEFAULT_WEIGHTS.copy())
        
        # Initialize component scorers
        self.skill_matcher = skill_matcher or SkillMatcher()
        self.experience_scorer = experience_scorer or ExperienceScorer()
        self.education_scorer = education_scorer or EducationScorer()
        self.explainer = explainer or ScoringExplainer()

    def _validate_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """
        Validate and normalize weights.

        Args:
            weights: Dictionary of component weights

        Returns:
            Validated and normalized weights

        Raises:
            ValueError: If weights are invalid
        """
        required_keys = ['skill_weight', 'experience_weight', 'education_weight']
        
        # Check all required keys present
        for key in required_keys:
            if key not in weights:
                raise ValueError(f"Missing weight: {key}")
        
        # Check all weights are non-negative
        for key, value in weights.items():
            if value < 0:
                raise ValueError(f"Negative weight not allowed: {key}={value}")
        
        # Normalize to sum to 1.0
        total = sum(weights[key] for key in required_keys)
        if total == 0:
            raise ValueError("Sum of weights cannot be zero")
        
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Weights sum to {total}, normalizing to 1.0"
            )
            normalized = {
                key: weights[key] / total
                for key in required_keys
            }
            return normalized
        
        return weights

    def score_candidate(
        self,
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive candidate score.

        Args:
            candidate_data: Complete candidate information including:
                - skills/technical_skills: List of skills
                - experience_years: Total years of experience
                - positions: List of past positions
                - education_level: Highest education level
                - education_field: Field of study
                - degrees: List of degrees
            criteria: Complete job requirements including:
                - required_skills/preferred_skills/bonus_skills: Skill requirements
                - min_experience_years/ideal_experience_years: Experience requirements
                - required_level/preferred_level: Education requirements
                - required_field/acceptable_fields: Field requirements
            weights: Optional weight override

        Returns:
            Dictionary with:
                - 'total_score': float between 0 and 100
                - 'component_scores': Dict of individual component scores
                - 'explanation': Human-readable explanation
                - 'details': Detailed breakdown
                - 'quality': Overall match quality
        """
        # Use provided weights or instance weights
        active_weights = self._validate_weights(
            weights if weights else self.weights
        )
        
        # Score each component
        skill_result = self.skill_matcher.calculate_score(
            candidate_data, criteria
        )
        experience_result = self.experience_scorer.calculate_score(
            candidate_data, criteria
        )
        education_result = self.education_scorer.calculate_score(
            candidate_data, criteria
        )
        
        # Calculate weighted total
        total_score = (
            skill_result['score'] * active_weights['skill_weight'] +
            experience_result['score'] * active_weights['experience_weight'] +
            education_result['score'] * active_weights['education_weight']
        ) * 100  # Scale to 0-100
        
        # Compile component scores
        component_scores = {
            'skills': skill_result['score'],
            'experience': experience_result['score'],
            'education': education_result['score'],
        }
        
        # Determine overall quality
        quality = self._determine_quality(total_score, component_scores)
        
        # Generate explanation
        explanation = self.explainer.generate_explanation(
            total_score=total_score,
            component_scores=component_scores,
            skill_details=skill_result,
            experience_details=experience_result,
            education_details=education_result,
            candidate_data=candidate_data,
            criteria=criteria,
        )
        
        # Compile detailed breakdown
        details = {
            'skills': skill_result['details'],
            'experience': experience_result['details'],
            'education': education_result['details'],
            'weights_used': active_weights,
            'matched_items': {
                'skills': skill_result['matched'],
                'experience': experience_result['matched'],
                'education': education_result['matched'],
            },
            'missing_items': {
                'skills': skill_result['missing'],
                'experience': experience_result['missing'],
                'education': education_result['missing'],
            },
        }
        
        return {
            'total_score': round(total_score, 2),
            'component_scores': {
                k: round(v, 3) for k, v in component_scores.items()
            },
            'explanation': explanation,
            'details': details,
            'quality': quality,
        }

    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple candidates based on criteria.

        Args:
            candidates: List of candidate data dictionaries (must have 'id' field)
            criteria: Job requirements
            weights: Optional weight configuration

        Returns:
            List of candidates sorted by score (highest first), each with:
                - All original candidate data
                - 'score': Calculated score
                - 'rank': Position in ranking (1-based)
                - 'explanation': Why this score was assigned
                - 'component_scores': Breakdown by component
                - 'quality': Match quality assessment
        """
        if not candidates:
            return []
        
        logger.info(f"Ranking {len(candidates)} candidates...")
        
        # Score all candidates
        scored_candidates = []
        for candidate in candidates:
            try:
                result = self.score_candidate(candidate, criteria, weights)
                
                # Merge result into candidate data
                scored_candidate = {
                    **candidate,
                    'score': result['total_score'],
                    'component_scores': result['component_scores'],
                    'explanation': result['explanation'],
                    'details': result['details'],
                    'quality': result['quality'],
                }
                scored_candidates.append(scored_candidate)
                
            except Exception as e:
                logger.error(
                    f"Error scoring candidate {candidate.get('id', 'unknown')}: {e}"
                )
                # Include candidate with 0 score
                scored_candidates.append({
                    **candidate,
                    'score': 0.0,
                    'explanation': f"Error during scoring: {str(e)}",
                    'quality': 'error',
                })
        
        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks
        for idx, candidate in enumerate(scored_candidates, start=1):
            candidate['rank'] = idx
        
        logger.info(
            f"Ranking complete. Top score: {scored_candidates[0]['score']:.2f}"
        )
        
        return scored_candidates

    def _determine_quality(
        self, total_score: float, component_scores: Dict[str, float]
    ) -> str:
        """
        Determine qualitative match assessment.

        Args:
            total_score: Total score (0-100)
            component_scores: Individual component scores (0-1.0)

        Returns:
            Quality string: 'excellent', 'strong', 'good', 'fair', 'weak', 'poor'
        """
        # Check if any component is critically low
        min_component = min(component_scores.values())
        
        if total_score >= 85 and min_component >= 0.7:
            return 'excellent'
        elif total_score >= 75 and min_component >= 0.6:
            return 'strong'
        elif total_score >= 65 and min_component >= 0.5:
            return 'good'
        elif total_score >= 50:
            return 'fair'
        elif total_score >= 30:
            return 'weak'
        else:
            return 'poor'

    def get_weights(self) -> Dict[str, float]:
        """Get current weight configuration."""
        return self.weights.copy()

    def set_weights(self, weights: Dict[str, float]):
        """
        Update weight configuration.

        Args:
            weights: New weights

        Raises:
            ValueError: If weights are invalid
        """
        self.weights = self._validate_weights(weights)
        logger.info(f"Updated weights: {self.weights}")


def create_scoring_engine(
    weights: Optional[Dict[str, float]] = None,
    fuzzy_threshold: int = 85,
    use_synonyms: bool = True,
    use_hierarchy: bool = True,
    experience_strategy: str = "diminishing_returns",
) -> WeightedScoringEngine:
    """
    Factory function to create a configured scoring engine.

    Args:
        weights: Component weights
        fuzzy_threshold: Fuzzy matching threshold (0-100)
        use_synonyms: Enable synonym matching
        use_hierarchy: Enable skill hierarchy matching
        experience_strategy: Experience scoring strategy

    Returns:
        Configured WeightedScoringEngine instance

    Example:
        >>> engine = create_scoring_engine(
        ...     weights={'skill_weight': 0.6, 'experience_weight': 0.3, 'education_weight': 0.1},
        ...     fuzzy_threshold=80,
        ... )
        >>> result = engine.score_candidate(candidate_data, criteria)
    """
    skill_matcher = SkillMatcher(
        fuzzy_threshold=fuzzy_threshold,
        use_synonyms=use_synonyms,
        use_hierarchy=use_hierarchy,
    )
    
    experience_scorer = ExperienceScorer(strategy=experience_strategy)
    
    education_scorer = EducationScorer()
    
    return WeightedScoringEngine(
        weights=weights,
        skill_matcher=skill_matcher,
        experience_scorer=experience_scorer,
        education_scorer=education_scorer,
    )
