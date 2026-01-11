"""Fuzzy matching and synonym handling for skills and keywords."""

from .fuzzy_matcher import FuzzyMatcher
from .synonym_dict import SKILL_SYNONYMS, get_synonyms
from .skill_taxonomy import SKILL_HIERARCHY, get_related_skills

__all__ = [
    'FuzzyMatcher',
    'SKILL_SYNONYMS',
    'get_synonyms',
    'SKILL_HIERARCHY',
    'get_related_skills',
]
