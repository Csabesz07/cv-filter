"""Setup phrase matchers for entity recognition."""

import logging
from spacy.matcher import PhraseMatcher
import spacy

from .entity_lists import (
    PROGRAMMING_LANGUAGES,
    FRAMEWORKS,
    DATABASES,
    CLOUD_PLATFORMS,
    TOOLS,
    NATURAL_LANGUAGES,
    ALL_JOB_TITLES,
    ALL_SOFT_SKILLS,
)

logger = logging.getLogger(__name__)


class MatcherFactory:
    """Factory for creating and configuring phrase matchers."""

    @staticmethod
    def create_phrase_matcher(nlp: "spacy.Language") -> PhraseMatcher:
        """
        Create and configure phrase matcher with entity patterns.

        Args:
            nlp: spaCy language model

        Returns:
            Configured PhraseMatcher instance
        """
        phrase_matcher = PhraseMatcher(nlp.vocab, attr="LOWER")

        # Add patterns to phrase matcher
        patterns_config = [
            ("PROGRAMMING_LANGUAGE", PROGRAMMING_LANGUAGES),
            ("FRAMEWORK", FRAMEWORKS),
            ("DATABASE", DATABASES),
            ("CLOUD", CLOUD_PLATFORMS),
            ("TOOL", TOOLS),
            ("SOFT_SKILL", ALL_SOFT_SKILLS),
            ("NATURAL_LANGUAGE", NATURAL_LANGUAGES),
            ("JOB_TITLE", ALL_JOB_TITLES),
        ]

        for category, terms in patterns_config:
            patterns = [nlp.make_doc(text) for text in terms]
            phrase_matcher.add(category, patterns)
            logger.debug(f"Added {len(terms)} patterns for {category}")

        logger.info(f"Phrase matcher configured with {len(patterns_config)} categories")
        return phrase_matcher

