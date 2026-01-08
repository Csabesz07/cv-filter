"""Main CV entity extraction module."""

import logging
import subprocess
from pathlib import Path

import spacy

from .models import ExtractedEntities
from .matchers import MatcherFactory
from .extractors import (
    ContactExtractor,
    SkillsExtractor,
    ExperienceExtractor,
    EducationExtractor,
    AdditionalExtractor,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVEntityExtractor:
    """
    NLP-based entity extractor for CV/Resume parsing.
    Extracts key entities relevant to job listings using spaCy NER,
    regex patterns, and custom matching.

    Main entities extracted:
    - Positions (job titles)
    - Skills (programming languages, frameworks, databases, tools, cloud platforms)
    - Qualifications (degrees, certifications)
    """

    def __init__(self, spacy_model: str = "en_core_web_sm"):
        """
        Initialize the entity extractor.

        Args:
            spacy_model: SpaCy model to use (default: en_core_web_sm)
        """
        self.spacy_model = spacy_model
        self.nlp = self._load_spacy_model(spacy_model)

        # Setup phrase matcher
        self.phrase_matcher = MatcherFactory.create_phrase_matcher(self.nlp)

        # Initialize extractors
        self.skills_extractor = SkillsExtractor(self.phrase_matcher)
        self.experience_extractor = ExperienceExtractor(self.phrase_matcher)
        self.education_extractor = EducationExtractor()
        self.additional_extractor = AdditionalExtractor(self.phrase_matcher)

    def _load_spacy_model(self, model_name: str) -> "spacy.Language":
        """
        Load spaCy model, downloading if necessary.

        Args:
            model_name: Name of the spaCy model

        Returns:
            Loaded spaCy language model
        """
        try:
            nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
            return nlp
        except OSError:
            logger.warning(f"Model {model_name} not found. Downloading...")
            subprocess.run(
                ["python", "-m", "spacy", "download", model_name],
                check=True,
                capture_output=True,
            )
            nlp = spacy.load(model_name)
            logger.info(f"Successfully downloaded and loaded spaCy model: {model_name}")
            return nlp

    def extract_entities(self, text: str) -> ExtractedEntities:
        """
        Extract all entities from CV text.

        Args:
            text: Extracted text from CV (as returned by CVTextExtractor)

        Returns:
            ExtractedEntities object with all extracted information
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for entity extraction")
            return ExtractedEntities.empty()

        # Process text with spaCy
        doc = self.nlp(text.lower())

        # Extract different types of entities
        contact_info = ContactExtractor.extract(text)
        technical_skills = self.skills_extractor.extract(doc)
        soft_skills = self.additional_extractor.extract_soft_skills(doc)
        languages = self.additional_extractor.extract_languages(doc)
        education = self.education_extractor.extract(text, doc)
        experience = self.experience_extractor.extract(text, doc)

        return ExtractedEntities(
            # Contact
            email=contact_info["email"],
            phone=contact_info["phone"],
            linkedin=contact_info["linkedin"],
            github=contact_info["github"],
            websites=contact_info["websites"],
            # Technical Skills
            programming_languages=technical_skills["programming_languages"],
            frameworks=technical_skills["frameworks"],
            databases=technical_skills["databases"],
            tools=technical_skills["tools"],
            cloud_platforms=technical_skills["cloud_platforms"],
            # Soft Skills
            soft_skills=soft_skills,
            # Languages
            languages=languages,
            # Education
            degrees=education["degrees"],
            certifications=education["certifications"],
            # Experience
            job_titles=experience["job_titles"],
        )

    def save_entities(
        self, entities: ExtractedEntities, output_path: str, indent: int = 2
    ) -> None:
        """
        Save extracted entities to JSON file.

        Args:
            entities: ExtractedEntities object to save
            output_path: Path where to save the JSON file
            indent: JSON indentation (default: 2)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(entities.to_json(indent=indent))

            logger.info(f"Saved extracted entities to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save entities to {output_path}: {str(e)}")
            raise
