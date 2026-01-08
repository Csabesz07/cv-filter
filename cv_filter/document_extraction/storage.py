"""Storage utilities for saving extracted text."""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalFileStorage:
    """Handles saving extracted text to local filesystem."""

    @staticmethod
    def save_extracted_text(
        original_file_path: Path, text: str, output_dir: Optional[Path] = None
    ) -> Path:
        """
        Save extracted text to a file.

        Args:
            original_file_path: Path to the original CV file
            text: Extracted text content
            output_dir: Optional directory to save the text file.
                       If None, saves in same directory as source file.

        Returns:
            Path to the saved text file

        Raises:
            IOError: If file cannot be written
        """
        # Get original filename without extension
        original_name = original_file_path.stem

        # Create output filename
        output_filename = f"{original_name}_extracted.txt"

        # Determine output directory
        if output_dir:
            output_path = output_dir / output_filename
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Save in same directory as source file
            output_path = original_file_path.parent / output_filename

        # Write text to file
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)

            logger.info(f"Saved extracted text to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to save text file {output_path}: {str(e)}")
            raise IOError(f"Failed to save text file: {str(e)}") from e


class DatabaseStorage:
    """
    Handles saving extracted text and original files to database.

    This is a placeholder for future database integration.
    The implementation will save to CVFile and CVParse models.
    """

    @staticmethod
    def save(cv_file, extracted_text: str, metadata: dict, method: str) -> None:
        """
        Save extracted text to database.

        Args:
            cv_file: CVFile model instance
            extracted_text: Extracted text content
            metadata: File metadata
            method: Extraction method used

        Note:
            This method is a placeholder for future implementation.
            It should create a CVParse instance linked to the CVFile.
        """
        # TODO: Implement database saving
        # This should create a CVParse instance with:
        # - cv_file: the CVFile instance
        # - text_content: extracted_text
        # - parser_name: method
        # - parse_status: CVParseStatus.SUCCEEDED
        # - metadata stored in appropriate fields
        pass
