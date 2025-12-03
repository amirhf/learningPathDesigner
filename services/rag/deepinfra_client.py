"""
Deep Infra API client for embeddings and reranking
"""
import httpx
import logging
from typing import List, Dict, Any

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DeepInfraClient:
    """HTTP client for Deep Infra API with error handling"""
    
    def __init__(self):
        if not settings.deepinfra_api_key:
            raise ValueError("DEEPINFRA_API_KEY is required when USE_DEEPINFRA=true")
        
        self.base_url = settings.deepinfra_base_url
        self.headers = {
            "Authorization": f"Bearer {settings.deepinfra_api_key}",
            "Content-Type": "application/json"
        }
        self.timeout = settings.inference_timeout
        logger.info(f"DeepInfraClient initialized with base_url={self.base_url}")
    
    def generate_embeddings_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings via Deep Infra API (synchronous)
        
        Args:
            texts: List of texts to embed (should already include query:/passage: prefix)
        
        Returns:
            List of embedding vectors
        """
        url = f"{self.base_url}/inference/{settings.deepinfra_embedding_model}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self.headers,
                    json={"inputs": texts}
                )
                response.raise_for_status()
                data = response.json()
                
                # Deep Infra returns embeddings directly
                return data["embeddings"]
                
        except httpx.TimeoutException as e:
            logger.error(f"Deep Infra embedding request timed out: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Deep Infra embedding API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Deep Infra embedding request failed: {e}")
            raise
    
    def rerank_sync(self, query: str, documents: List[str]) -> List[float]:
        """
        Rerank documents via Deep Infra API (synchronous)
        
        Args:
            query: Search query
            documents: List of document texts to rerank
        
        Returns:
            List of relevance scores (one per document)
        """
        url = f"{self.base_url}/inference/{settings.deepinfra_reranker_model}"
        
        # Qwen reranker API expects: {"queries": [...], "documents": [...]}
        # For single query, we send the same query for all documents
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    url,
                    headers=self.headers,
                    json={
                        "queries": [query],
                        "documents": documents
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # Qwen reranker returns {"scores": [...]}
                if "scores" in data:
                    return [float(s) for s in data["scores"]]
                else:
                    logger.warning(f"Unexpected rerank response format: {data}")
                    return [0.0] * len(documents)
                    
        except httpx.TimeoutException as e:
            logger.error(f"Deep Infra rerank request timed out: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"Deep Infra rerank API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Deep Infra rerank request failed: {e}")
            raise
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Async version for future use"""
        url = f"{self.base_url}/inference/{settings.deepinfra_embedding_model}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json={"inputs": texts}
            )
            response.raise_for_status()
            return response.json()["embeddings"]
    
    async def rerank(self, query: str, documents: List[str]) -> List[float]:
        """Async version for future use"""
        url = f"{self.base_url}/inference/{settings.deepinfra_reranker_model}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                headers=self.headers,
                json={
                    "queries": [query],
                    "documents": documents
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if "scores" in data:
                return [float(s) for s in data["scores"]]
            return [0.0] * len(documents)


# Singleton instance
_client = None


def get_deepinfra_client() -> DeepInfraClient:
    """Get or create Deep Infra client instance"""
    global _client
    if _client is None:
        _client = DeepInfraClient()
    return _client
