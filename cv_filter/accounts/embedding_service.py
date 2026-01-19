"""Embedding generation service for semantic search."""

import logging
from typing import List, Optional
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using sentence-transformers."""
    
    _model = None
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"  # 384 dimensions
    
    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Get or initialize the embedding model (singleton)."""
        if cls._model is None:
            logger.info(f"Loading embedding model: {cls.MODEL_NAME}")
            cls._model = SentenceTransformer(cls.MODEL_NAME)
            logger.info("Embedding model loaded successfully")
        return cls._model
    
    @classmethod
    def generate_embedding(cls, text: str) -> Optional[List[float]]:
        """
        Generate embedding vector for a given text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector, or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return None
            
        try:
            model = cls.get_model()
            # Generate embedding
            embedding = model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return None
    
    @classmethod
    def generate_embeddings_batch(cls, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
            
        try:
            model = cls.get_model()
            embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            return [None] * len(texts)
