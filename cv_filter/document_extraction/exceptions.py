"""Custom exceptions for document extraction."""


class ExtractionException(Exception):
    """Base exception for extraction errors."""

    pass


class TimeoutException(ExtractionException):
    """Exception raised when operation times out."""

    pass


class UnsupportedFileFormatException(ExtractionException):
    """Exception raised when file format is not supported."""

    pass


class FileValidationException(ExtractionException):
    """Exception raised when file validation fails."""

    pass



