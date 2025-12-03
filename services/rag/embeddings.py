"""
Embedding generation with Deep Infra API or local fallback
"""
import logging
from typing import List

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class EmbeddingService:
    """Service for generating embeddings via API or local model"""
    
    def __init__(self):
        self.use_deepinfra = settings.use_deepinfra
        self._local_model = None  # Lazy loaded only if needed
        self._deepinfra_client = None
        
        if self.use_deepinfra:
            logger.info("EmbeddingService initialized with Deep Infra API")
        else:
            logger.info("EmbeddingService initialized with local PyTorch model")
    
    def _get_deepinfra_client(self):
        """Lazy load Deep Infra client"""
        if self._deepinfra_client is None:
            from deepinfra_client import get_deepinfra_client
            self._deepinfra_client = get_deepinfra_client()
        return self._deepinfra_client
    
    def _load_local_model(self):
        """Load local PyTorch model (fallback)"""
        if self._local_model is None:
            import torch
            from sentence_transformers import SentenceTransformer
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading local embedding model: {settings.embedding_model} on {device}")
            
            self._local_model = SentenceTransformer(settings.embedding_model, device=device)
            
            # Apply quantization if enabled
            if settings.use_quantization and settings.quantization_config != "none":
                if device == "cpu":
                    self._local_model[0].auto_model = torch.quantization.quantize_dynamic(
                        self._local_model[0].auto_model,
                        {torch.nn.Linear},
                        dtype=torch.qint8
                    )
                    logger.info("✓ Applied INT8 quantization")
                else:
                    if hasattr(self._local_model, 'half'):
                        self._local_model = self._local_model.half()
                        logger.info("✓ Using FP16 precision")
            
            logger.info("✓ Local embedding model ready")
        
        return self._local_model
    
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
        # Add instruction prefix for e5 models
        prefix = "query: " if instruction == "query" else "passage: "
        prefixed_texts = [f"{prefix}{text}" for text in texts]
        
        if self.use_deepinfra:
            return self._generate_via_api(prefixed_texts)
        else:
            return self._generate_local(prefixed_texts)
    
    def _generate_via_api(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings via Deep Infra API"""
        client = self._get_deepinfra_client()
        return client.generate_embeddings_sync(texts)
    
    def _generate_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model"""
        model = self._load_local_model()
        embeddings = model.encode(
            texts,
            batch_size=16,
            show_progress_bar=False,
            convert_to_numpy=True
        )
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
