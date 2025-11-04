"""
Embedding generation using e5-base-v2
"""
import logging
from typing import List
from sentence_transformers import SentenceTransformer
import torch

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings"""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
    
    def load_model(self):
        """Load the embedding model"""
        if self.model is None:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            self.model = SentenceTransformer(settings.embedding_model, device=self.device)
            logger.info("Embedding model loaded successfully")
    
    def generate_embeddings(
        self,
        texts: List[str],
        instruction: str = "passage"
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            instruction: Instruction prefix ('query' or 'passage')
        
        Returns:
            List of embedding vectors
        """
        if self.model is None:
            self.load_model()
        
        # Add instruction prefix for e5 models
        if instruction == "query":
            prefixed_texts = [f"query: {text}" for text in texts]
        else:
            prefixed_texts = [f"passage: {text}" for text in texts]
        
        # Generate embeddings
        embeddings = self.model.encode(
            prefixed_texts,
            batch_size=16,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # Convert to list of lists
        return embeddings.tolist()
    
    def generate_single_embedding(self, text: str, instruction: str = "passage") -> List[float]:
        """Generate embedding for a single text"""
        return self.generate_embeddings([text], instruction)[0]


# Global instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
