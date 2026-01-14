"""Extract additional information like soft skills, languages, projects, and awards."""

import logging
from typing import Dict, List
from spacy.tokens import Doc

logger = logging.getLogger(__name__)


class AdditionalExtractor:
    """Extracts additional information from CV text."""

    def __init__(self, phrase_matcher):
        """
        Initialize the additional extractor.

        Args:
            phrase_matcher: spaCy PhraseMatcher instance
        """
        self.phrase_matcher = phrase_matcher

    def extract_soft_skills(self, doc: Doc) -> List[str]:
        """
        Extract soft skills from text.

        Args:
            doc: spaCy processed document

        Returns:
            List of soft skills found
        """
        matches = self.phrase_matcher(doc)
        soft_skills = set()

        for match_id, start, end in matches:
            label = doc.vocab.strings[match_id]
            if label == "SOFT_SKILL":
                span = doc[start:end]
                soft_skills.add(span.text)

        return sorted(list(soft_skills))

    def extract_languages(self, doc: Doc) -> List[str]:
        """
        Extract natural languages.

        Args:
            doc: spaCy processed document

        Returns:
            List of languages found
        """
        matches = self.phrase_matcher(doc)
        languages = set()

        for match_id, start, end in matches:
            label = doc.vocab.strings[match_id]
            if label == "NATURAL_LANGUAGE":
                span = doc[start:end]
                languages.add(span.text)

        return sorted(list(languages))

    def extract_projects_and_awards(self, text: str, doc: Doc) -> Dict[str, List[str]]:
        """
        Extract projects and awards.

        Args:
            text: Original text
            doc: spaCy processed document

        Returns:
            Dictionary with keys: projects, awards
        """
        projects = []
        awards = []

        text_lower = text.lower()

        # Look for project sections
        project_keywords = ["project", "developed", "built", "created", "implemented"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in project_keywords):
                projects.append(sent.text.strip())

        # Look for awards/achievements
        award_keywords = ["award", "achievement", "honor", "recognition", "winner"]
        for sent in doc.sents:
            if any(keyword in sent.text.lower() for keyword in award_keywords):
                awards.append(sent.text.strip())

        return {
            "projects": projects[:5],  # Limit to 5 most relevant
            "awards": awards[:5],
        }

