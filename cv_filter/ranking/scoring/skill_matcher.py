"""
Skill matching and scoring component.
Handles exact matching, fuzzy matching, synonym expansion, and hierarchical relationships.
"""

import logging
from typing import Any, Dict, List, Set, Tuple

from .base import ComponentScorer
from ..matching.fuzzy_matcher import FuzzyMatcher
from ..matching.synonym_dict import get_synonyms, normalize_skill, expand_skills
from ..matching.skill_taxonomy import (
    get_related_skills,
    implies_skill,
    calculate_skill_distance,
)

logger = logging.getLogger(__name__)


class SkillMatcher(ComponentScorer):
    """
    Skill matching and scoring component.
    Supports multiple matching strategies:
    - Exact matching
    - Fuzzy matching (typo tolerance)
    - Synonym matching
    - Hierarchical/taxonomy matching
    """

    def __init__(
        self,
        fuzzy_threshold: int = 85,
        use_synonyms: bool = True,
        use_hierarchy: bool = True,
    ):
        """
        Initialize skill matcher.

        Args:
            fuzzy_threshold: Minimum fuzzy match score (0-100)
            use_synonyms: Whether to use synonym expansion
            use_hierarchy: Whether to use skill hierarchy/taxonomy
        """
        self.fuzzy_matcher = FuzzyMatcher(threshold=fuzzy_threshold)
        self.use_synonyms = use_synonyms
        self.use_hierarchy = use_hierarchy

    def calculate_score(
        self,
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate skill match score.

        Args:
            candidate_data: {
                'skills': ['Python', 'Django', 'PostgreSQL', 'Docker'],
                'technical_skills': [...],  # alternative key
            }
            criteria: {
                'required_skills': ['Python', 'Django', 'REST API'],
                'preferred_skills': ['Docker', 'Kubernetes'],
                'bonus_skills': ['AWS', 'Terraform'],
            }

        Returns:
            {
                'score': 0.85,  # 0-1.0
                'details': {
                    'required_matched': 2,
                    'required_total': 3,
                    'preferred_matched': 1,
                    'preferred_total': 2,
                    'bonus_matched': 0,
                    'bonus_total': 2,
                },
                'matched': ['Python', 'Django', 'Docker'],
                'missing': ['REST API', 'Kubernetes'],
                'extra': ['PostgreSQL'],
            }
        """
        # Extract candidate skills
        candidate_skills = self._extract_skills(candidate_data)
        
        # Normalize skills
        candidate_skills_normalized = self._normalize_skills(candidate_skills)
        
        # Extract criteria
        required_skills = criteria.get('required_skills', [])
        preferred_skills = criteria.get('preferred_skills', [])
        bonus_skills = criteria.get('bonus_skills', [])
        
        # Match each tier
        required_result = self._match_skill_tier(
            required_skills, candidate_skills_normalized, weight=1.0
        )
        preferred_result = self._match_skill_tier(
            preferred_skills, candidate_skills_normalized, weight=0.6
        )
        bonus_result = self._match_skill_tier(
            bonus_skills, candidate_skills_normalized, weight=0.3
        )
        
        # Calculate weighted score
        total_weighted_matches = (
            required_result['weighted_matches'] +
            preferred_result['weighted_matches'] +
            bonus_result['weighted_matches']
        )
        
        total_weighted_possible = (
            required_result['weighted_total'] +
            preferred_result['weighted_total'] +
            bonus_result['weighted_total']
        )
        
        # Avoid division by zero
        if total_weighted_possible == 0:
            score = 1.0 if len(candidate_skills) > 0 else 0.0
        else:
            score = total_weighted_matches / total_weighted_possible
        
        # Collect all matched and missing skills
        all_matched = (
            required_result['matched'] +
            preferred_result['matched'] +
            bonus_result['matched']
        )
        all_missing = (
            required_result['missing'] +
            preferred_result['missing'] +
            bonus_result['missing']
        )
        
        # Extra skills (not in any criteria)
        all_criteria_skills = set(required_skills + preferred_skills + bonus_skills)
        all_criteria_normalized = self._normalize_skills(list(all_criteria_skills))
        extra_skills = [
            skill for skill in candidate_skills
            if normalize_skill(skill) not in all_criteria_normalized
        ]
        
        return {
            'score': min(1.0, score),  # Cap at 1.0
            'details': {
                'required_matched': required_result['matches'],
                'required_total': required_result['total'],
                'preferred_matched': preferred_result['matches'],
                'preferred_total': preferred_result['total'],
                'bonus_matched': bonus_result['matches'],
                'bonus_total': bonus_result['total'],
                'match_quality': self._calculate_match_quality(required_result, preferred_result),
            },
            'matched': all_matched,
            'missing': all_missing,
            'extra': extra_skills,
        }

    def _extract_skills(self, candidate_data: Dict[str, Any]) -> List[str]:
        """Extract skills from candidate data."""
        # Try multiple possible keys
        for key in ['skills', 'technical_skills', 'skill_list']:
            if key in candidate_data and candidate_data[key]:
                skills = candidate_data[key]
                if isinstance(skills, list):
                    return skills
                elif isinstance(skills, str):
                    return [s.strip() for s in skills.split(',')]
        
        return []

    def _normalize_skills(self, skills: List[str]) -> Set[str]:
        """Normalize list of skills."""
        return {normalize_skill(skill) for skill in skills}

    def _match_skill_tier(
        self,
        required: List[str],
        candidate_skills: Set[str],
        weight: float,
    ) -> Dict[str, Any]:
        """
        Match a tier of skills (required/preferred/bonus).

        Returns:
            {
                'matches': 2,
                'total': 3,
                'weighted_matches': 2.0,
                'weighted_total': 3.0,
                'matched': ['Python', 'Django'],
                'missing': ['REST API'],
            }
        """
        if not required:
            return {
                'matches': 0,
                'total': 0,
                'weighted_matches': 0.0,
                'weighted_total': 0.0,
                'matched': [],
                'missing': [],
            }
        
        matched = []
        missing = []
        
        for skill in required:
            if self._is_match(skill, candidate_skills):
                matched.append(skill)
            else:
                missing.append(skill)
        
        return {
            'matches': len(matched),
            'total': len(required),
            'weighted_matches': len(matched) * weight,
            'weighted_total': len(required) * weight,
            'matched': matched,
            'missing': missing,
        }

    def _is_match(self, required_skill: str, candidate_skills: Set[str]) -> bool:
        """
        Check if required skill matches any candidate skill.
        Uses multiple strategies: exact, fuzzy, synonym, hierarchy.
        """
        required_normalized = normalize_skill(required_skill)
        
        # 1. Exact match (normalized)
        if required_normalized in candidate_skills:
            return True
        
        # 2. Synonym match
        if self.use_synonyms:
            required_synonyms = get_synonyms(required_skill)
            if required_synonyms & candidate_skills:  # Intersection
                return True
        
        # 3. Fuzzy match
        for candidate_skill in candidate_skills:
            if self.fuzzy_matcher.match(required_skill, candidate_skill):
                return True
        
        # 4. Hierarchy match (candidate skill implies required skill)
        if self.use_hierarchy:
            for candidate_skill in candidate_skills:
                if implies_skill(candidate_skill, required_skill):
                    return True
        
        return False

    def _calculate_match_quality(
        self, required_result: Dict, preferred_result: Dict
    ) -> str:
        """
        Calculate qualitative match assessment.

        Returns:
            'excellent', 'strong', 'good', 'fair', 'weak'
        """
        required_rate = (
            required_result['matches'] / required_result['total']
            if required_result['total'] > 0
            else 1.0
        )
        preferred_rate = (
            preferred_result['matches'] / preferred_result['total']
            if preferred_result['total'] > 0
            else 0.0
        )
        
        if required_rate == 1.0 and preferred_rate >= 0.7:
            return 'excellent'
        elif required_rate >= 0.9 and preferred_rate >= 0.5:
            return 'strong'
        elif required_rate >= 0.7:
            return 'good'
        elif required_rate >= 0.5:
            return 'fair'
        else:
            return 'weak'

    def get_skill_similarity_matrix(
        self, skills1: List[str], skills2: List[str]
    ) -> Dict[Tuple[str, str], float]:
        """
        Calculate similarity matrix between two skill lists.

        Args:
            skills1: First list of skills
            skills2: Second list of skills

        Returns:
            Dictionary mapping (skill1, skill2) -> similarity_score (0-1.0)
        """
        matrix = {}
        
        for s1 in skills1:
            for s2 in skills2:
                # Combine multiple similarity measures
                similarity = 0.0
                
                # Exact match
                if normalize_skill(s1) == normalize_skill(s2):
                    similarity = 1.0
                # Synonym match
                elif self.use_synonyms and get_synonyms(s1) & get_synonyms(s2):
                    similarity = 0.95
                # Fuzzy match
                else:
                    fuzzy_score = self.fuzzy_matcher.similarity(s1, s2) / 100.0
                    similarity = max(similarity, fuzzy_score)
                
                # Hierarchy distance
                if self.use_hierarchy:
                    distance = calculate_skill_distance(s1, s2)
                    if distance == 1:  # Parent-child
                        similarity = max(similarity, 0.7)
                    elif distance == 2:  # Siblings
                        similarity = max(similarity, 0.5)
                
                matrix[(s1, s2)] = similarity
        
        return matrix
