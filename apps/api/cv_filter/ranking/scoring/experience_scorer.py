"""
Experience scoring component.
Evaluates candidate experience based on years and relevance.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base import ComponentScorer

logger = logging.getLogger(__name__)


class ExperienceScorer(ComponentScorer):
    """
    Experience scoring component.
    Supports multiple scoring strategies for years of experience.
    """

    def __init__(self, strategy: str = "diminishing_returns"):
        """
        Initialize experience scorer.

        Args:
            strategy: Scoring strategy to use
                - "linear": Linear scaling up to ideal years
                - "threshold": Binary threshold-based
                - "diminishing_returns": Exponential diminishing returns (default)
        """
        self.strategy = strategy

    def calculate_score(
        self,
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate experience score.

        Args:
            candidate_data: {
                'experience_years': 5.5,
                'total_experience': 5.5,  # alternative key
                'positions': [
                    {'title': 'Backend Developer', 'years': 3},
                    {'title': 'Python Developer', 'years': 2.5}
                ]
            }
            criteria: {
                'min_experience_years': 3,
                'ideal_experience_years': 7,
                'target_role': 'Senior Python Developer',
                'relevant_titles': ['Python Developer', 'Backend Developer']
            }

        Returns:
            {
                'score': 0.85,  # 0-1.0
                'details': {
                    'candidate_years': 5.5,
                    'required_minimum': 3,
                    'ideal_years': 7,
                    'meets_minimum': True,
                    'relevance_score': 0.9,
                },
                'matched': ['Backend Developer experience', '5+ years total'],
                'missing': ['Senior-level experience'],
            }
        """
        # Extract candidate experience
        candidate_years = self._extract_experience_years(candidate_data)
        positions = candidate_data.get('positions', [])
        
        # Extract criteria
        min_years = criteria.get('min_experience_years', 0)
        ideal_years = criteria.get('ideal_experience_years')
        target_role = criteria.get('target_role')
        relevant_titles = criteria.get('relevant_titles', [])
        
        # Calculate years-based score
        years_score = self._score_years(
            candidate_years, min_years, ideal_years
        )
        
        # Calculate relevance score
        relevance_score = self._score_relevance(
            positions, target_role, relevant_titles
        ) if positions else 1.0
        
        # Combine scores (70% years, 30% relevance)
        final_score = (years_score * 0.7) + (relevance_score * 0.3)
        
        # Determine matches and gaps
        matched, missing = self._analyze_experience_gaps(
            candidate_years, min_years, ideal_years, positions, target_role
        )
        
        return {
            'score': min(1.0, final_score),
            'details': {
                'candidate_years': float(candidate_years),
                'required_minimum': float(min_years),
                'ideal_years': float(ideal_years) if ideal_years else None,
                'meets_minimum': candidate_years >= min_years,
                'years_score': years_score,
                'relevance_score': relevance_score,
            },
            'matched': matched,
            'missing': missing,
        }

    def _extract_experience_years(self, candidate_data: Dict[str, Any]) -> Decimal:
        """Extract total years of experience from candidate data."""
        # Try multiple possible keys
        for key in ['experience_years', 'total_experience', 'years_of_experience']:
            if key in candidate_data and candidate_data[key] is not None:
                value = candidate_data[key]
                if isinstance(value, (int, float, Decimal)):
                    return Decimal(str(value))
        
        # Calculate from positions if available
        positions = candidate_data.get('positions', [])
        if positions:
            total = sum(
                Decimal(str(pos.get('years', 0)))
                for pos in positions
                if 'years' in pos
            )
            return total
        
        return Decimal('0')

    def _score_years(
        self,
        candidate_years: Decimal,
        min_years: float,
        ideal_years: Optional[float] = None,
    ) -> float:
        """
        Score based on years of experience.

        Args:
            candidate_years: Candidate's total years
            min_years: Minimum required years
            ideal_years: Ideal years (optional)

        Returns:
            Score between 0.0 and 1.0
        """
        candidate_years_float = float(candidate_years)
        
        if self.strategy == "linear":
            return self._score_linear(candidate_years_float, min_years, ideal_years)
        elif self.strategy == "threshold":
            return self._score_threshold(candidate_years_float, min_years)
        elif self.strategy == "diminishing_returns":
            return self._score_diminishing_returns(
                candidate_years_float, min_years, ideal_years
            )
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

    def _score_linear(
        self, candidate_years: float, min_years: float, ideal_years: Optional[float]
    ) -> float:
        """Linear scoring strategy."""
        target = ideal_years if ideal_years else min_years
        
        if candidate_years >= target:
            return 1.0
        elif candidate_years < min_years:
            # Partial credit below minimum
            return max(0.3, (candidate_years / min_years) * 0.7)
        else:
            # Between min and ideal: linear interpolation
            return 0.7 + ((candidate_years - min_years) / (target - min_years)) * 0.3

    def _score_threshold(self, candidate_years: float, min_years: float) -> float:
        """Threshold-based scoring (binary)."""
        if candidate_years >= min_years:
            return 1.0
        else:
            # Partial credit for being close
            if candidate_years >= min_years * 0.8:
                return 0.7
            elif candidate_years >= min_years * 0.5:
                return 0.5
            else:
                return 0.3

    def _score_diminishing_returns(
        self, candidate_years: float, min_years: float, ideal_years: Optional[float]
    ) -> float:
        """
        Diminishing returns strategy.
        
        Logic:
        - < min_years: Partial credit with steep penalty
        - min to ideal: High growth
        - > ideal: Plateau (no extra benefit beyond ideal)
        """
        if candidate_years < min_years:
            # Below minimum: partial credit
            ratio = candidate_years / max(min_years, 1)
            return max(0.2, ratio * 0.6)
        
        if ideal_years and candidate_years >= ideal_years:
            # At or above ideal: full score
            return 1.0
        
        # Between min and ideal (or just above min if no ideal)
        if ideal_years:
            # Exponential curve from 0.6 to 1.0
            progress = (candidate_years - min_years) / (ideal_years - min_years)
            # Using square root for diminishing returns
            return 0.6 + (progress ** 0.7) * 0.4
        else:
            # No ideal specified: plateau after 2x minimum
            if candidate_years >= min_years * 2:
                return 1.0
            else:
                progress = (candidate_years - min_years) / min_years
                return 0.7 + (progress ** 0.8) * 0.3

    def _score_relevance(
        self,
        positions: List[Dict[str, Any]],
        target_role: Optional[str],
        relevant_titles: List[str],
    ) -> float:
        """
        Score relevance of past positions to target role.

        Args:
            positions: List of past positions
            target_role: Target job title
            relevant_titles: List of relevant job titles

        Returns:
            Relevance score 0-1.0
        """
        if not positions:
            return 0.5  # Neutral if no data
        
        if not target_role and not relevant_titles:
            return 1.0  # No criteria, assume relevant
        
        # Count relevant positions
        relevant_count = 0
        total_years_relevant = 0
        total_years = 0
        
        for position in positions:
            title = position.get('title', '')
            years = position.get('years', 0)
            total_years += years
            
            is_relevant = False
            
            # Check against target role
            if target_role and self._title_similarity(title, target_role) > 0.6:
                is_relevant = True
            
            # Check against relevant titles
            for relevant_title in relevant_titles:
                if self._title_similarity(title, relevant_title) > 0.6:
                    is_relevant = True
                    break
            
            if is_relevant:
                relevant_count += 1
                total_years_relevant += years
        
        # Score based on proportion of relevant experience
        if total_years > 0:
            year_ratio = total_years_relevant / total_years
            position_ratio = relevant_count / len(positions)
            # Weighted average (years matter more)
            return (year_ratio * 0.7) + (position_ratio * 0.3)
        
        return 0.5

    def _title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between job titles.

        Args:
            title1: First job title
            title2: Second job title

        Returns:
            Similarity score 0-1.0
        """
        if not title1 or not title2:
            return 0.0
        
        t1_lower = title1.lower()
        t2_lower = title2.lower()
        
        # Exact match
        if t1_lower == t2_lower:
            return 1.0
        
        # Common keywords
        keywords = ['senior', 'junior', 'lead', 'principal', 'developer', 
                   'engineer', 'programmer', 'architect', 'backend', 'frontend',
                   'full stack', 'python', 'javascript', 'java']
        
        t1_keywords = [kw for kw in keywords if kw in t1_lower]
        t2_keywords = [kw for kw in keywords if kw in t2_lower]
        
        if not t1_keywords or not t2_keywords:
            # Fallback: simple word overlap
            t1_words = set(t1_lower.split())
            t2_words = set(t2_lower.split())
            if t1_words & t2_words:
                return len(t1_words & t2_words) / max(len(t1_words), len(t2_words))
            return 0.0
        
        # Jaccard similarity of keywords
        common = len(set(t1_keywords) & set(t2_keywords))
        total = len(set(t1_keywords) | set(t2_keywords))
        
        return common / total if total > 0 else 0.0

    def _analyze_experience_gaps(
        self,
        candidate_years: Decimal,
        min_years: float,
        ideal_years: Optional[float],
        positions: List[Dict[str, Any]],
        target_role: Optional[str],
    ) -> tuple:
        """
        Analyze what experience requirements are met and which are missing.

        Returns:
            (matched_list, missing_list)
        """
        matched = []
        missing = []
        
        candidate_years_float = float(candidate_years)
        
        # Check minimum requirement
        if candidate_years_float >= min_years:
            matched.append(f"{candidate_years_float:.1f} years of experience (meets {min_years}+ requirement)")
        else:
            missing.append(f"Minimum {min_years} years (has {candidate_years_float:.1f})")
        
        # Check ideal
        if ideal_years:
            if candidate_years_float >= ideal_years:
                matched.append(f"Meets ideal experience ({ideal_years}+ years)")
            else:
                gap = ideal_years - candidate_years_float
                missing.append(f"{gap:.1f} years to reach ideal ({ideal_years} years)")
        
        # Check role relevance
        if target_role and positions:
            has_similar = any(
                self._title_similarity(pos.get('title', ''), target_role) > 0.6
                for pos in positions
            )
            if has_similar:
                matched.append(f"Relevant experience in {target_role}")
            else:
                missing.append(f"Direct experience as {target_role}")
        
        return matched, missing
