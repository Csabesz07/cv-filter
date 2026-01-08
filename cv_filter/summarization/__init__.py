"""CV summarization package for generating candidate summaries."""

from .summarizer import CVSummarizer
from .models import CVSummary

__all__ = [
    "CVSummarizer",
    "CVSummary",
]

