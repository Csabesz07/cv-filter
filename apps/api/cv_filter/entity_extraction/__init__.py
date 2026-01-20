"""Entity extraction package for CV entity recognition."""

from .entity_extractor import CVEntityExtractor
from .models import ExtractedEntities

__all__ = [
    "CVEntityExtractor",
    "ExtractedEntities",
]

