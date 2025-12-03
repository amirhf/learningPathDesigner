"""
Reranking with Deep Infra API or local fallback
"""
import logging
from typing import List, Dict, Any, Tuple

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RerankService:
    """Service for reranking search results via API or local model"""
    
    def __init__(self):
        self.use_deepinfra = settings.use_deepinfra
        self._local_model = None  # Lazy loaded only if needed
        self._deepinfra_client = None
        
        if self.use_deepinfra:
            logger.info("RerankService initialized with Deep Infra API")
        else:
            logger.info("RerankService initialized with local CrossEncoder model")
    
    def _get_deepinfra_client(self):
        """Lazy load Deep Infra client"""
        if self._deepinfra_client is None:
            from deepinfra_client import get_deepinfra_client
            self._deepinfra_client = get_deepinfra_client()
        return self._deepinfra_client
    
    def _load_local_model(self):
        """Load local CrossEncoder model (fallback)"""
        if self._local_model is None:
            import torch
            from sentence_transformers import CrossEncoder
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Loading local reranker model: {settings.reranker_model} on {device}")
            
            self._local_model = CrossEncoder(settings.reranker_model, device=device)
            
            # Apply quantization if enabled
            if settings.use_quantization and settings.quantization_config != "none":
                if device == "cpu":
                    if hasattr(self._local_model, 'model'):
                        self._local_model.model = torch.quantization.quantize_dynamic(
                            self._local_model.model,
                            {torch.nn.Linear},
                            dtype=torch.qint8
                        )
                        logger.info("✓ Applied INT8 quantization to reranker")
                else:
                    if hasattr(self._local_model, 'model') and hasattr(self._local_model.model, 'half'):
                        self._local_model.model = self._local_model.model.half()
                        logger.info("✓ Using FP16 precision for reranker")
            
            logger.info("✓ Local reranker model ready")
        
        return self._local_model
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[float]]:
        """
        Rerank documents using cross-encoder
        
        Args:
            query: Search query
            documents: List of documents to rerank
            top_n: Number of top results to return
        
        Returns:
            Tuple of (reranked_documents, scores)
        """
        if not documents:
            return [], []
        
        # Extract text from documents
        doc_texts = []
        for doc in documents:
            doc_text = doc.get("title", "")
            if doc.get("description"):
                doc_text += " " + doc["description"]
            doc_texts.append(doc_text)
        
        # Get scores via API or local model
        if self.use_deepinfra:
            scores = self._rerank_via_api(query, doc_texts)
        else:
            scores = self._rerank_local(query, doc_texts)
        
        # Sort by score (descending)
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        top_docs = [doc for doc, _ in scored_docs[:top_n]]
        top_scores = [float(score) for _, score in scored_docs[:top_n]]
        
        return top_docs, top_scores
    
    def _rerank_via_api(self, query: str, doc_texts: List[str]) -> List[float]:
        """Rerank via Deep Infra API"""
        client = self._get_deepinfra_client()
        return client.rerank_sync(query, doc_texts)
    
    def _rerank_local(self, query: str, doc_texts: List[str]) -> List[float]:
        """Rerank using local model"""
        model = self._load_local_model()
        pairs = [[query, text] for text in doc_texts]
        scores = model.predict(pairs, show_progress_bar=False)
        return list(scores)


# Global instance
_rerank_service = None


def get_rerank_service() -> RerankService:
    """Get or create rerank service instance"""
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService()
    return _rerank_service
