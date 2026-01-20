"""
Education scoring component.
Evaluates candidate education level and field relevance.
"""

import logging
from typing import Any, Dict, List, Optional

from .base import ComponentScorer

logger = logging.getLogger(__name__)


# Education level hierarchy
EDUCATION_LEVELS = {
    "none": 0,
    "high_school": 1,
    "associate": 2,
    "bachelor": 3,
    "master": 4,
    "phd": 5,
    "doctorate": 5,  # Alias for phd
}

# Field relevance scores for tech positions
FIELD_RELEVANCE = {
    # Highly relevant
    "computer_science": 1.0,
    "software_engineering": 1.0,
    "computer_engineering": 1.0,
    "information_technology": 0.95,
    "information_systems": 0.95,
    
    # Related STEM
    "electrical_engineering": 0.9,
    "mathematics": 0.85,
    "statistics": 0.85,
    "data_science": 0.95,
    "physics": 0.8,
    "engineering": 0.75,
    
    # Somewhat relevant
    "business": 0.6,
    "economics": 0.6,
    "management": 0.55,
    
    # Less relevant
    "other": 0.5,
}


class EducationScorer(ComponentScorer):
    """
    Education scoring component.
    Evaluates both education level and field relevance.
    """

    def __init__(
        self,
        level_weight: float = 0.6,
        relevance_weight: float = 0.4,
    ):
        """
        Initialize education scorer.

        Args:
            level_weight: Weight for education level (0-1.0)
            relevance_weight: Weight for field relevance (0-1.0)
        """
        self.level_weight = level_weight
        self.relevance_weight = relevance_weight
        
        # Validate weights
        total = level_weight + relevance_weight
        if abs(total - 1.0) > 0.01:
            logger.warning(
                f"Education weights don't sum to 1.0: {total}. "
                f"Normalizing to {level_weight/total} and {relevance_weight/total}"
            )
            self.level_weight = level_weight / total
            self.relevance_weight = relevance_weight / total

    def calculate_score(
        self,
        candidate_data: Dict[str, Any],
        criteria: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate education score.

        Args:
            candidate_data: {
                'education_level': 'master',
                'education_field': 'computer_science',
                'degrees': [
                    {
                        'level': 'bachelor',
                        'field': 'computer_science',
                        'institution': 'MIT'
                    },
                    {
                        'level': 'master',
                        'field': 'computer_science',
                        'institution': 'Stanford'
                    }
                ]
            }
            criteria: {
                'required_level': 'bachelor',
                'preferred_level': 'master',
                'required_field': 'computer_science',
                'acceptable_fields': ['computer_science', 'software_engineering']
            }

        Returns:
            {
                'score': 0.95,  # 0-1.0
                'details': {
                    'candidate_level': 'master',
                    'required_level': 'bachelor',
                    'level_score': 1.0,
                    'field_score': 1.0,
                    'meets_requirement': True,
                },
                'matched': ['Master in Computer Science', 'Exceeds minimum requirement'],
                'missing': [],
            }
        """
        # Extract candidate education
        candidate_level = self._extract_level(candidate_data)
        candidate_field = self._extract_field(candidate_data)
        degrees = candidate_data.get('degrees', [])
        
        # Extract criteria
        required_level = criteria.get('required_level', 'bachelor')
        preferred_level = criteria.get('preferred_level')
        required_field = criteria.get('required_field')
        acceptable_fields = criteria.get('acceptable_fields', [])
        
        # Calculate level score
        level_score = self._score_level(
            candidate_level, required_level, preferred_level
        )
        
        # Calculate field relevance score
        field_score = self._score_field(
            candidate_field, required_field, acceptable_fields, degrees
        )
        
        # Combine scores
        final_score = (
            level_score * self.level_weight +
            field_score * self.relevance_weight
        )
        
        # Determine matches and gaps
        matched, missing = self._analyze_education_gaps(
            candidate_level, candidate_field,
            required_level, preferred_level,
            required_field, acceptable_fields
        )
        
        return {
            'score': min(1.0, final_score),
            'details': {
                'candidate_level': candidate_level,
                'candidate_field': candidate_field,
                'required_level': required_level,
                'preferred_level': preferred_level,
                'level_score': level_score,
                'field_score': field_score,
                'meets_requirement': level_score >= 0.7,
            },
            'matched': matched,
            'missing': missing,
        }

    def _extract_level(self, candidate_data: Dict[str, Any]) -> str:
        """Extract highest education level from candidate data."""
        # Try direct field
        if 'education_level' in candidate_data:
            return self._normalize_level(candidate_data['education_level'])
        
        # Try degrees list
        degrees = candidate_data.get('degrees', [])
        if degrees:
            highest = max(
                degrees,
                key=lambda d: EDUCATION_LEVELS.get(
                    self._normalize_level(d.get('level', 'none')), 0
                )
            )
            return self._normalize_level(highest.get('level', 'none'))
        
        return 'none'

    def _extract_field(self, candidate_data: Dict[str, Any]) -> Optional[str]:
        """Extract education field from candidate data."""
        # Try direct field
        if 'education_field' in candidate_data:
            return self._normalize_field(candidate_data['education_field'])
        
        # Try highest degree's field
        degrees = candidate_data.get('degrees', [])
        if degrees:
            # Get field from highest degree
            highest = max(
                degrees,
                key=lambda d: EDUCATION_LEVELS.get(
                    self._normalize_level(d.get('level', 'none')), 0
                )
            )
            field = highest.get('field')
            if field:
                return self._normalize_field(field)
        
        return None

    def _normalize_level(self, level: str) -> str:
        """Normalize education level string."""
        if not level:
            return 'none'
        
        level_lower = level.lower().strip()
        
        # Handle variations
        aliases = {
            "high school": "high_school",
            "hs": "high_school",
            "associate degree": "associate",
            "bachelor's": "bachelor",
            "bachelor degree": "bachelor",
            "bs": "bachelor",
            "ba": "bachelor",
            "master's": "master",
            "master degree": "master",
            "ms": "master",
            "ma": "master",
            "mba": "master",
            "phd": "phd",
            "ph.d.": "phd",
            "doctorate": "phd",
        }
        
        if level_lower in EDUCATION_LEVELS:
            return level_lower
        
        for alias, canonical in aliases.items():
            if alias in level_lower:
                return canonical
        
        return 'none'

    def _normalize_field(self, field: str) -> str:
        """Normalize education field string."""
        if not field:
            return 'other'
        
        field_lower = field.lower().strip()
        
        # Handle variations
        aliases = {
            "cs": "computer_science",
            "compsci": "computer_science",
            "comp sci": "computer_science",
            "it": "information_technology",
            "is": "information_systems",
            "ee": "electrical_engineering",
            "math": "mathematics",
            "stats": "statistics",
        }
        
        if field_lower in FIELD_RELEVANCE:
            return field_lower
        
        for alias, canonical in aliases.items():
            if alias in field_lower or canonical.replace('_', ' ') in field_lower:
                return canonical
        
        return 'other'

    def _score_level(
        self,
        candidate_level: str,
        required_level: str,
        preferred_level: Optional[str] = None,
    ) -> float:
        """
        Score education level.

        Args:
            candidate_level: Candidate's education level
            required_level: Minimum required level
            preferred_level: Preferred level (optional)

        Returns:
            Score 0-1.0
        """
        candidate_rank = EDUCATION_LEVELS.get(candidate_level, 0)
        required_rank = EDUCATION_LEVELS.get(
            self._normalize_level(required_level), 0
        )
        preferred_rank = (
            EDUCATION_LEVELS.get(self._normalize_level(preferred_level), required_rank)
            if preferred_level
            else required_rank
        )
        
        # Below minimum
        if candidate_rank < required_rank:
            # Partial credit for being close
            if candidate_rank == required_rank - 1:
                return 0.7  # One level below
            else:
                return 0.5  # Multiple levels below
        
        # Meets minimum
        if candidate_rank == required_rank:
            return 0.85
        
        # Between minimum and preferred
        if preferred_rank > required_rank and candidate_rank < preferred_rank:
            progress = (candidate_rank - required_rank) / (preferred_rank - required_rank)
            return 0.85 + (progress * 0.15)
        
        # Meets or exceeds preferred
        return 1.0

    def _score_field(
        self,
        candidate_field: Optional[str],
        required_field: Optional[str],
        acceptable_fields: List[str],
        degrees: List[Dict[str, Any]],
    ) -> float:
        """
        Score field relevance.

        Args:
            candidate_field: Candidate's primary field
            required_field: Required field
            acceptable_fields: List of acceptable fields
            degrees: List of all degrees

        Returns:
            Score 0-1.0
        """
        # No field requirement
        if not required_field and not acceptable_fields:
            # Use general tech relevance
            if candidate_field:
                return FIELD_RELEVANCE.get(candidate_field, 0.5)
            return 0.7  # Neutral if no data
        
        # Check exact match
        if required_field and candidate_field == self._normalize_field(required_field):
            return 1.0
        
        # Check acceptable fields
        normalized_acceptable = [
            self._normalize_field(f) for f in acceptable_fields
        ]
        if candidate_field in normalized_acceptable:
            return 1.0
        
        # Check all degrees (maybe a second degree matches)
        for degree in degrees:
            degree_field = self._normalize_field(degree.get('field', ''))
            if required_field and degree_field == self._normalize_field(required_field):
                return 0.95  # Slightly lower if not primary degree
            if degree_field in normalized_acceptable:
                return 0.95
        
        # Use relevance score
        if candidate_field:
            return FIELD_RELEVANCE.get(candidate_field, 0.5)
        
        return 0.5  # Neutral if no data

    def _analyze_education_gaps(
        self,
        candidate_level: str,
        candidate_field: Optional[str],
        required_level: str,
        preferred_level: Optional[str],
        required_field: Optional[str],
        acceptable_fields: List[str],
    ) -> tuple:
        """
        Analyze education matches and gaps.

        Returns:
            (matched_list, missing_list)
        """
        matched = []
        missing = []
        
        candidate_rank = EDUCATION_LEVELS.get(candidate_level, 0)
        required_rank = EDUCATION_LEVELS.get(
            self._normalize_level(required_level), 0
        )
        
        # Check level
        if candidate_rank >= required_rank:
            if candidate_level != 'none':
                matched.append(f"{candidate_level.replace('_', ' ').title()} degree")
            if preferred_level:
                preferred_rank = EDUCATION_LEVELS.get(
                    self._normalize_level(preferred_level), 0
                )
                if candidate_rank >= preferred_rank:
                    matched.append(f"Meets preferred level ({preferred_level})")
        else:
            missing.append(
                f"Minimum {required_level.replace('_', ' ')} degree "
                f"(has {candidate_level.replace('_', ' ')})"
            )
        
        # Check field
        if required_field or acceptable_fields:
            field_names = [required_field] if required_field else acceptable_fields
            normalized_fields = [self._normalize_field(f) for f in field_names if f]
            
            if candidate_field in normalized_fields:
                matched.append(
                    f"Relevant field: {candidate_field.replace('_', ' ').title()}"
                )
            else:
                if candidate_field:
                    relevance = FIELD_RELEVANCE.get(candidate_field, 0)
                    if relevance >= 0.8:
                        matched.append(f"Related field: {candidate_field.replace('_', ' ').title()}")
                    else:
                        missing.append(f"Preferred field: {', '.join(f.replace('_', ' ') for f in field_names)}")
                else:
                    missing.append("Field information not available")
        
        return matched, missing
