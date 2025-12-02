"""
Qdrant search functionality
"""
import logging
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range, PointStruct
import uuid

from config import get_settings
from embeddings import get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()


class SearchService:
    """Service for searching resources in Qdrant"""
    
    def __init__(self):
        self.client = None
        self.embedding_service = get_embedding_service()
    
    def connect(self):
        """Connect to Qdrant"""
        if self.client is None:
            logger.info(f"Connecting to Qdrant at {settings.qdrant_url}")
            self.client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key,
                timeout=30
            )
            logger.info("Connected to Qdrant successfully")
    
    def build_filter(self, search_filter: Optional[Dict[str, Any]] = None) -> Optional[Filter]:
        """Build Qdrant filter from search parameters"""
        if not search_filter:
            # Default to global only if no filter provided? Or allow all?
            # Safer to default to global for now if we want isolation by default.
            return Filter(must=[FieldCondition(key="tenant_id", match=MatchValue(value="global"))])
        
        conditions = []
        
        # Tenant filter: (tenant_id = 'global' OR tenant_id = current_tenant)
        tenant_id = search_filter.get("tenant_id", "global")
        if tenant_id == "global":
            conditions.append(
                FieldCondition(
                    key="tenant_id",
                    match=MatchValue(value="global")
                )
            )
        else:
            # OR condition
            conditions.append(
                Filter(
                    should=[
                        FieldCondition(key="tenant_id", match=MatchValue(value="global")),
                        FieldCondition(key="tenant_id", match=MatchValue(value=tenant_id))
                    ]
                )
            )
        
        # Level filter (less than or equal)
        if search_filter.get("level") is not None:
            conditions.append(
                FieldCondition(
                    key="level",
                    range=Range(lte=search_filter["level"])
                )
            )
        
        # Duration filter (less than or equal)
        if search_filter.get("max_duration_min"):
            conditions.append(
                FieldCondition(
                    key="duration_min",
                    range=Range(lte=search_filter["max_duration_min"])
                )
            )
        
        # Media type filter
        if search_filter.get("media_type"):
            conditions.append(
                FieldCondition(
                    key="media_type",
                    match=MatchValue(value=search_filter["media_type"])
                )
            )
        
        # Provider filter
        if search_filter.get("provider"):
            conditions.append(
                FieldCondition(
                    key="provider",
                    match=MatchValue(value=search_filter["provider"])
                )
            )
        
        if not conditions:
            return None
        
        return Filter(must=conditions)
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for resources using semantic search
        
        Args:
            query: Search query
            filters: Optional filters
            top_k: Number of results to return
        
        Returns:
            List of search results with scores
        """
        if self.client is None:
            self.connect()
        
        # Generate query embedding
        query_embedding = self.embedding_service.generate_single_embedding(
            query,
            instruction="query"
        )
        
        # Build filter
        qdrant_filter = self.build_filter(filters)
        
        # Search
        try:
            search_result = self.client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_embedding,
                query_filter=qdrant_filter,
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            results = []
            for hit in search_result:
                result = {
                    "resource_id": hit.payload.get("resource_id") or str(hit.id),
                    "title": hit.payload.get("title"),
                    "url": hit.payload.get("url"),
                    "provider": hit.payload.get("provider"),
                    "license": hit.payload.get("license"),
                    "duration_min": hit.payload.get("duration_min"),
                    "level": hit.payload.get("level"),
                    "skills": hit.payload.get("skills", []),
                    "media_type": hit.payload.get("media_type"),
                    "score": hit.score
                }
                results.append(result)
            
            return results
        
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise
    
    def upsert_resource(
        self,
        resource_id: str,
        embedding: List[float],
        payload: Dict[str, Any]
    ):
        """Upsert a resource into Qdrant"""
        if self.client is None:
            self.connect()
        
        point = PointStruct(
            id=resource_id,
            vector=embedding,
            payload=payload
        )
        
        self.client.upsert(
            collection_name=settings.qdrant_collection,
            points=[point]
        )
    
    def health_check(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            if self.client is None:
                self.connect()
            collections = self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False


# Global instance
_search_service = None


def get_search_service() -> SearchService:
    """Get or create search service instance"""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
