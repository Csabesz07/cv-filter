"""Extract contact information from text."""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContactExtractor:
    """Extracts contact information from CV text."""

    @staticmethod
    def extract(text: str) -> Dict[str, List[str]]:
        """
        Extract contact information using regex patterns.

        Args:
            text: Input text to extract from

        Returns:
            Dictionary with keys: email, phone, linkedin, github, websites
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for contact extraction")
            return {
                "email": [],
                "phone": [],
                "linkedin": [],
                "github": [],
                "websites": [],
            }

        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = list(set(re.findall(email_pattern, text)))

        # Phone pattern (various formats)
        phone_pattern = r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
        phone_matches = re.findall(phone_pattern, text)
        phones = [" ".join(p).strip() if isinstance(p, tuple) else p for p in phone_matches]
        phones = list(set(p for p in phones if p.strip()))

        # LinkedIn
        linkedin_pattern = r"linkedin\.com/in/[\w-]+"
        linkedin = list(set(re.findall(linkedin_pattern, text.lower())))

        # GitHub
        github_pattern = r"github\.com/[\w-]+"
        github = list(set(re.findall(github_pattern, text.lower())))

        # Websites (general URLs)
        url_pattern = (
            r"https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b"
            r"(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
        )
        urls = list(set(re.findall(url_pattern, text)))
        # Remove linkedin and github from general websites
        websites = [
            url
            for url in urls
            if "linkedin.com" not in url.lower() and "github.com" not in url.lower()
        ]

        return {
            "email": sorted(emails),
            "phone": sorted(phones),
            "linkedin": sorted(linkedin),
            "github": sorted(github),
            "websites": sorted(websites),
        }

