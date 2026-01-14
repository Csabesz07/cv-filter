"""Data models for CV summarization."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class CVSummary:
    """Data class to store CV summary."""

    summary_text: str
    language: str = "en"
    generated_at: Optional[datetime] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    prompt_version: Optional[str] = None

    def __post_init__(self):
        """Set generated_at if not provided."""
        if self.generated_at is None:
            self.generated_at = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "summary_text": self.summary_text,
            "language": self.language,
            "generated_at": (
                self.generated_at.isoformat() if self.generated_at else None
            ),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_version": self.prompt_version,
        }

