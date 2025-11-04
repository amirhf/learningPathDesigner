"""
Pydantic models for RAG service
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class EmbedRequest(BaseModel):
    """Request to generate embeddings"""
    texts: List[str] = Field(..., description="List of texts to embed")
    instruction: str = Field(default="passage", description="Instruction prefix: 'query' or 'passage'")


class EmbedResponse(BaseModel):
    """Response with embeddings"""
    embeddings: List[List[float]] = Field(..., description="List of embedding vectors")
    dimension: int = Field(..., description="Embedding dimension")
    model: str = Field(..., description="Model used")


class SearchFilter(BaseModel):
    """Filters for search"""
    level: Optional[int] = Field(None, ge=0, le=2, description="Skill level (0=beginner, 1=intermediate, 2=advanced)")
    max_duration_min: Optional[int] = Field(None, gt=0, description="Maximum duration in minutes")
    skills: Optional[List[str]] = Field(None, description="Required skill UUIDs")
    media_type: Optional[str] = Field(None, description="Media type filter")
    provider: Optional[str] = Field(None, description="Provider filter")


class SearchRequest(BaseModel):
    """Request to search resources"""
    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[SearchFilter] = Field(None, description="Search filters")
    top_k: int = Field(default=20, ge=1, le=50, description="Number of results to return")
    rerank: bool = Field(default=True, description="Whether to apply reranking")
    rerank_top_n: int = Field(default=5, ge=1, le=20, description="Number of results after reranking")


class ResourceResult(BaseModel):
    """Search result for a resource"""
    resource_id: str
    title: str
    url: str
    provider: Optional[str] = None
    license: Optional[str] = None
    duration_min: Optional[int] = None
    level: Optional[int] = None
    skills: List[str] = []
    media_type: Optional[str] = None
    score: float
    why_relevant: Optional[str] = None


class SearchResponse(BaseModel):
    """Response with search results"""
    results: List[ResourceResult]
    query: str
    total_found: int
    reranked: bool


class RerankRequest(BaseModel):
    """Request to rerank results"""
    query: str = Field(..., description="Original query")
    documents: List[Dict[str, Any]] = Field(..., description="Documents to rerank")
    top_n: int = Field(default=5, ge=1, le=20, description="Number of top results to return")


class RerankResponse(BaseModel):
    """Response with reranked results"""
    results: List[Dict[str, Any]]
    scores: List[float]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    qdrant_connected: bool
    models_loaded: bool
