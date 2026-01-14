"""Main CV text extraction module."""

import logging
import signal
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Optional, Any

try:
    from .exceptions import TimeoutException
    from .extractors import PDFExtractor, DOCXExtractor
    from .file_validator import FileValidator
    from .storage import LocalFileStorage
except ImportError:
    import sys
    from pathlib import Path

    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from exceptions import TimeoutException
    from extractors import PDFExtractor, DOCXExtractor
    from file_validator import FileValidator
    from storage import LocalFileStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@contextmanager
def timeout(seconds):
    """
    Context manager for timeout operations on Unix-like systems.

    Note: Timeout is not available on Windows.
    """

    def timeout_handler(signum, frame):
        raise TimeoutException("Operation timed out")

    # Set the signal handler and alarm (main thread only)
    if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, original_handler)
    else:  # Windows or non-main thread - no timeout available
        yield


class CVTextExtractor:
    """
    Text extraction from CV files in PDF and DOCX formats.
    Uses PyMuPDF for fast, reliable PDF extraction without Java dependencies.
    """

    def __init__(
        self,
        timeout_seconds: int = 30,
        save_to_file: bool = True,
        output_dir: Optional[str] = None,
    ):
        """
        Initialize the text extractor.

        Args:
            timeout_seconds: Maximum time allowed for extraction per file
            save_to_file: Whether to automatically save extracted text to files
            output_dir: Directory to save extracted text files (default: same as source)
        """
        self.timeout_seconds = timeout_seconds
        self.save_to_file = save_to_file
        self.output_dir = Path(output_dir) if output_dir else None

        # Create output directory if specified
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_text(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from CV file (PDF or DOCX).

        Args:
            file_path: Path to the CV file

        Returns:
            Dictionary containing:
                - 'text': Extracted text content
                - 'metadata': File metadata (if available)
                - 'success': Boolean indicating extraction success
                - 'error': Error message if extraction failed
                - 'method': Extraction method used
                - 'output_file': Path to saved text file (if save_to_file is True)
        """
        file_path = Path(file_path)

        # Validate file
        is_valid, error_message = FileValidator.validate_file(file_path)
        if not is_valid:
            return {
                "text": "",
                "metadata": {},
                "success": False,
                "error": error_message,
                "method": None,
                "output_file": None,
            }

        # Determine file type and extract
        file_extension = file_path.suffix.lower()

        try:
            with timeout(self.timeout_seconds):
                if file_extension == ".pdf":
                    result = PDFExtractor.extract(str(file_path))
                elif file_extension in [".docx", ".doc"]:
                    result = DOCXExtractor.extract(str(file_path))
                else:
                    # This should not happen due to validation, but handle it anyway
                    return {
                        "text": "",
                        "metadata": {},
                        "success": False,
                        "error": f"Unsupported file format: {file_extension}",
                        "method": None,
                        "output_file": None,
                    }

                # Save to file if extraction was successful
                if result["success"] and self.save_to_file:
                    try:
                        output_path = LocalFileStorage.save_extracted_text(
                            file_path, result["text"], self.output_dir
                        )
                        result["output_file"] = str(output_path)
                    except Exception as e:
                        logger.error(f"Failed to save extracted text: {str(e)}")
                        result["output_file"] = None
                else:
                    result["output_file"] = None

                return result

        except TimeoutException:
            logger.error(f"Extraction timeout for {file_path}")
            return {
                "text": "",
                "metadata": {},
                "success": False,
                "error": f"Extraction timed out after {self.timeout_seconds} seconds",
                "method": None,
                "output_file": None,
            }
        except Exception as e:
            logger.error(f"Unexpected error extracting text from {file_path}: {str(e)}")
            return {
                "text": "",
                "metadata": {},
                "success": False,
                "error": f"Extraction error: {str(e)}",
                "method": None,
                "output_file": None,
            }

    def batch_extract(
        self, file_paths: list, show_progress: bool = True
    ) -> Dict[str, Dict]:
        """
        Extract text from multiple files.

        Args:
            file_paths: List of file paths to process
            show_progress: Whether to log progress information

        Returns:
            Dictionary mapping file paths to extraction results
        """
        results = {}
        total = len(file_paths)

        for idx, file_path in enumerate(file_paths, 1):
            if show_progress:
                logger.info(f"Processing {idx}/{total}: {Path(file_path).name}")

            results[file_path] = self.extract_text(file_path)

        # Log summary
        if show_progress:
            successful = sum(1 for r in results.values() if r["success"])
            failed = total - successful
            logger.info(
                f"Batch extraction complete: {successful}/{total} successful, {failed} failed"
            )

        return results
