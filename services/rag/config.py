"""
Configuration management for RAG service
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Service
    service_name: str = "rag-service"
    environment: str = "production"
    log_level: str = "info"
    port: int = 8001  # Default for local, Cloud Run overrides with PORT env var
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/learnpath"
    
    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "resources"
    
    # Models (local inference)
    embedding_model: str = "intfloat/e5-base-v2"
    reranker_model: str = "BAAI/bge-reranker-base"
    embedding_dimension: int = 768
    
    # Deep Infra API (serverless inference)
    use_deepinfra: bool = True  # Feature flag: True = API, False = local PyTorch
    deepinfra_api_key: str | None = None
    deepinfra_base_url: str = "https://api.deepinfra.com/v1"
    deepinfra_embedding_model: str = "intfloat/e5-base-v2"
    deepinfra_reranker_model: str = "Qwen/Qwen3-Reranker-0.6B"
    inference_timeout: float = 30.0
    
    # Quantization settings (only used when use_deepinfra=False)
    use_quantization: bool = True
    quantization_config: str = "int8"  # Options: int8, int4, none
    
    # Search
    top_k: int = 20
    rerank_k: int = 5
    max_context_tokens: int = 4000
    
    class Config:
        env_file = ".env.local"
        case_sensitive = False
        extra = "ignore"  # Allow extra env vars not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
