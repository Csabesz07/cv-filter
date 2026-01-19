"""Extract education information from text."""

import re
import logging
from typing import Dict, List
from spacy.tokens import Doc

from ..entity_lists import ALL_DEGREE_PATTERNS

logger = logging.getLogger(__name__)


class EducationExtractor:
    """Extracts education information from CV text."""

    def extract(self, text: str, doc: Doc) -> Dict[str, List[str]]:
        """
        Extract education information.

        Args:
            text: Original text
            doc: spaCy processed document

        Returns:
            Dictionary with keys: degrees, certifications
        """
        degrees = set()
        certifications = set()

        text_lower = text.lower()

        # Extract degrees using patterns
        for degree in ALL_DEGREE_PATTERNS:
            pattern = r"\b" + re.escape(degree) + r"\b"
            if re.search(pattern, text_lower):
                degrees.add(degree)

        # Extract certifications (look for certification keywords)
        cert_pattern = (
            r"(?:certified|certification|certificate)[\s\w]*(?:in|for)?[\s]*"
            r"([\w\s]{3,30})"
        )
        cert_matches = re.findall(cert_pattern, text_lower)
        if cert_matches:
            certifications.update(cert_matches)

        return {
            "degrees": sorted(list(degrees)),
            "certifications": sorted(list(certifications)),
        }

