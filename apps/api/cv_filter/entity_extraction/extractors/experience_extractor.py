"""Extract work experience information from text."""

import logging
from typing import Dict
from spacy.tokens import Doc

logger = logging.getLogger(__name__)


class ExperienceExtractor:
    """Extracts work experience information from CV text."""

    def __init__(self, phrase_matcher):
        """
        Initialize the experience extractor.

        Args:
            phrase_matcher: spaCy PhraseMatcher instance
        """
        self.phrase_matcher = phrase_matcher

    def extract(self, text: str, doc: Doc) -> Dict:
        """
        Extract work experience information.

        Args:
            text: Original text
            doc: spaCy processed document

        Returns:
            Dictionary with key: job_titles
        """
        matches = self.phrase_matcher(doc)
        job_titles = set()

        # Extract job titles from phrase matching
        for match_id, start, end in matches:
            label = doc.vocab.strings[match_id]
            if label == "JOB_TITLE":
                span = doc[start:end]
                job_titles.add(span.text)

        return {
            "job_titles": sorted(list(job_titles)),
        }

