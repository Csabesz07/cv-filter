"""Extract technical skills from text."""

import logging
from typing import Dict, List
from spacy.tokens import Doc

from ..entity_lists import (
    PROGRAMMING_LANGUAGES,
    FRAMEWORKS,
    DATABASES,
    TOOLS,
    CLOUD_PLATFORMS,
)

logger = logging.getLogger(__name__)


class SkillsExtractor:
    """Extracts technical skills from CV text using phrase matching."""

    def __init__(self, phrase_matcher):
        """
        Initialize the skills extractor.

        Args:
            phrase_matcher: spaCy PhraseMatcher instance
        """
        self.phrase_matcher = phrase_matcher

    def extract(self, doc: Doc) -> Dict[str, List[str]]:
        """
        Extract technical skills using phrase matching.

        Args:
            doc: spaCy processed document

        Returns:
            Dictionary with keys: programming_languages, frameworks, databases,
            tools, cloud_platforms
        """
        matches = self.phrase_matcher(doc)

        technical = {
            "programming_languages": set(),
            "frameworks": set(),
            "databases": set(),
            "tools": set(),
            "cloud_platforms": set(),
        }

        for match_id, start, end in matches:
            label = doc.vocab.strings[match_id]
            span = doc[start:end]
            matched_text = span.text

            if label == "PROGRAMMING_LANGUAGE":
                technical["programming_languages"].add(matched_text)
            elif label == "FRAMEWORK":
                technical["frameworks"].add(matched_text)
            elif label == "DATABASE":
                technical["databases"].add(matched_text)
            elif label == "CLOUD":
                technical["cloud_platforms"].add(matched_text)
            elif label == "TOOL":
                technical["tools"].add(matched_text)

        # Convert sets to sorted lists
        return {k: sorted(list(v)) for k, v in technical.items()}

