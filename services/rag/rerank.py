"""
Reranking using cross-encoder model
"""
import logging
from typing import List, Dict, Any, Tuple
from sentence_transformers import CrossEncoder
import torch

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RerankService:
    """Service for reranking search results"""
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Reranker using device: {self.device}")
    
    def load_model(self):
        """Load the reranking model"""
        if self.model is None:
            logger.info(f"Loading reranker model: {settings.reranker_model}")
            self.model = CrossEncoder(settings.reranker_model, device=self.device)
            logger.info("Reranker model loaded successfully")
    
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
        if self.model is None:
            self.load_model()
        
        if not documents:
            return [], []
        
        # Prepare query-document pairs
        pairs = []
        for doc in documents:
            # Use title and description for reranking
            doc_text = doc.get("title", "")
            if doc.get("description"):
                doc_text += " " + doc["description"]
            pairs.append([query, doc_text])
        
        # Get scores
        scores = self.model.predict(pairs, show_progress_bar=False)
        
        # Sort by score (descending)
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        top_docs = [doc for doc, _ in scored_docs[:top_n]]
        top_scores = [float(score) for _, score in scored_docs[:top_n]]
        
        return top_docs, top_scores


# Global instance
_rerank_service = None


def get_rerank_service() -> RerankService:
    """Get or create rerank service instance"""
    global _rerank_service
    if _rerank_service is None:
        _rerank_service = RerankService()
    return _rerank_service
