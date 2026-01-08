"""Main CV summarization module."""

import logging
from typing import Optional
from datetime import datetime

from .models import CVSummary
from .template_builder import SummaryTemplateBuilder

try:
    from ..entity_extraction.models import ExtractedEntities
except ImportError:
    import sys
    from pathlib import Path

    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from entity_extraction.models import ExtractedEntities

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CVSummarizer:
    """
    CV summarization module.
    Generates 3-5 sentence summaries from extracted entities.
    Ensures no hallucinations by only using extracted data.
    """

    def __init__(
        self,
        language: str = "hu",
        model_name: str = "template-based",
        model_version: str = "1.0",
        prompt_version: str = "1.0",
    ):
        """
        Initialize the summarizer.

        Args:
            language: Language for summaries (default: "hu" for Hungarian, supports "en" for English)
            model_name: Name of the summarization model/approach
            model_version: Version of the model
            prompt_version: Version of the prompt template
        """
        self.language = language
        self.model_name = model_name
        self.model_version = model_version
        self.prompt_version = prompt_version
        self.template_builder = SummaryTemplateBuilder()

        logger.info(
            f"Initialized CVSummarizer (model: {model_name} v{model_version}, "
            f"language: {language})"
        )

    def generate_summary(
        self,
        entities: ExtractedEntities,
        language: Optional[str] = None,
    ) -> CVSummary:
        """
        Generate a summary from extracted entities.

        Args:
            entities: ExtractedEntities object containing all extracted data
            language: Optional language override (uses instance default if None)

        Returns:
            CVSummary object with the generated summary

        Raises:
            ValueError: If entities is empty or invalid
        """
        if not entities:
            raise ValueError("ExtractedEntities cannot be empty")

        summary_lang = language or self.language

        logger.info(f"Generating summary in {summary_lang}...")

        # Generate summary using template builder
        summary_text = self.template_builder.build_summary(entities, summary_lang)

        # Validate summary length (should be 3-5 sentences)
        # Handle both English (.) and Hungarian (.) sentence endings
        sentences = summary_text.split(". ")
        # Remove empty strings and ensure proper sentence endings
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = len(sentences)
        if sentence_count < 3:
            logger.warning(
                f"Summary has only {sentence_count} sentences, "
                f"expected 3-5 sentences"
            )
        elif sentence_count > 5:
            logger.warning(
                f"Summary has {sentence_count} sentences, "
                f"expected maximum 5 sentences. Truncating..."
            )
            # Truncate to 5 sentences
            sentences = sentences[:5]
            summary_text = ". ".join(sentences) + "."

        # Ensure proper sentence separation (Hungarian uses space after period)
        summary_text = summary_text.replace("..", ".")

        return CVSummary(
            summary_text=summary_text.strip(),
            language=summary_lang,
            generated_at=datetime.now(),
            model_name=self.model_name,
            model_version=self.model_version,
            prompt_version=self.prompt_version,
        )

    def save_summary(
        self, summary: CVSummary, output_path: str, indent: int = 2
    ) -> None:
        """
        Save summary to a file.

        Args:
            summary: CVSummary object to save
            output_path: Path where to save the summary file
            indent: JSON indentation (default: 2)

        Raises:
            IOError: If file cannot be written
        """
        from pathlib import Path
        import json

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(summary.to_dict(), f, indent=indent, ensure_ascii=False)

            logger.info(f"Saved summary to: {output_path}")
        except Exception as e:
            logger.error(f"Failed to save summary to {output_path}: {str(e)}")
            raise IOError(f"Failed to save summary: {str(e)}") from e
