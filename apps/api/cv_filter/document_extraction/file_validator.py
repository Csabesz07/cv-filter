"""File validation utilities for document extraction."""

import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class FileValidator:
    """Validates files before extraction."""

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc"}

    @staticmethod
    def validate_file(file_path: Path) -> Tuple[bool, str]:
        """
        Validate that a file exists and meets requirements.

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple of (is_valid, error_message)
            If valid, error_message will be empty string
        """
        if not file_path.exists():
            return False, f"File not found: {file_path}"

        try:
            file_size = file_path.stat().st_size
        except OSError as e:
            return False, f"Unable to read file: {str(e)}"

        if file_size > FileValidator.MAX_FILE_SIZE:
            return (
                False,
                f"File too large: {file_size} bytes (max {FileValidator.MAX_FILE_SIZE})",
            )

        file_extension = file_path.suffix.lower()
        if file_extension not in FileValidator.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported file format: {file_extension}"

        return True, ""

    @staticmethod
    def is_supported_format(file_path: Path) -> bool:
        """Check if file format is supported."""
        return file_path.suffix.lower() in FileValidator.SUPPORTED_EXTENSIONS
