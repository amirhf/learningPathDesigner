"""
Configuration management for RAG service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Service
    service_name: str = "rag-service"
    log_level: str = "info"
    port: int = 8001  # Default for local, Cloud Run overrides with PORT env var
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/learnpath"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "resources"
    
    # Models
    embedding_model: str = "intfloat/e5-base-v2"
    reranker_model: str = "BAAI/bge-reranker-base"
    embedding_dimension: int = 768
    
    # Quantization settings
    use_quantization: bool = True
    quantization_config: str = "int8"  # Options: int8, int4, none
    
    # Search
    default_top_k: int = 20
    default_rerank_top_n: int = 5
    max_top_k: int = 50
    
    class Config:
        env_file = ".env.local"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
