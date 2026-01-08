"""
Abstract base classes for scoring components.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ComponentScorer(ABC):
    """
    Abstract base class for individual scoring components.
    Each component (skills, experience, education) implements this interface.
    """

    @abstractmethod
    def calculate_score(
        self,
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate score for a specific component.

        Args:
            candidate_data: Dictionary containing candidate information
            criteria: Dictionary containing job requirements/criteria

        Returns:
            Dictionary with:
                - 'score': float between 0.0 and 1.0
                - 'details': Dict with component-specific breakdown
                - 'matched': List of matched items
                - 'missing': List of missing/unmatched items
        """
        pass


class ScoringEngine(ABC):
    """
    Abstract base class for complete scoring engines.
    Aggregates multiple component scorers into a final score.
    """

    @abstractmethod
    def score_candidate(
        self,
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive candidate score.

        Args:
            candidate_data: Complete candidate information
            criteria: Complete job requirements
            weights: Optional weight configuration for components

        Returns:
            Dictionary with:
                - 'total_score': float between 0 and 100
                - 'component_scores': Dict of individual component scores
                - 'explanation': Human-readable explanation
                - 'details': Detailed breakdown
        """
        pass

    @abstractmethod
    def rank_candidates(
        self,
        candidates: List[Dict[str, Any]],
        criteria: Dict[str, Any],
        weights: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple candidates based on criteria.

        Args:
            candidates: List of candidate data dictionaries
            criteria: Job requirements
            weights: Optional weight configuration

        Returns:
            List of candidates sorted by score (highest first), each with:
                - All original candidate data
                - 'score': Calculated score
                - 'rank': Position in ranking (1-based)
                - 'explanation': Why this score was assigned
        """
        pass


class ScoringResult:
    """
    Standardized result object for scoring operations.
    """

    def __init__(
        self,
        total_score: float,
        component_scores: Dict[str, float],
        details: Dict[str, Any],
        explanation: str = "",
    ):
        """
        Initialize scoring result.

        Args:
            total_score: Final aggregated score (0-100)
            component_scores: Individual component scores (0-1.0)
            details: Detailed breakdown of scoring
            explanation: Human-readable explanation
        """
        self.total_score = total_score
        self.component_scores = component_scores
        self.details = details
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'total_score': round(self.total_score, 2),
            'component_scores': {
                k: round(v, 3) for k, v in self.component_scores.items()
            },
            'details': self.details,
            'explanation': self.explanation,
        }

    def __repr__(self):
        return f"ScoringResult(total={self.total_score:.1f})"
