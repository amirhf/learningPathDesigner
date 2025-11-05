"""
Download and cache models during Docker build for faster startup
Quantization is applied at runtime (still fast, ~2-3s)
"""
import logging
import os
from sentence_transformers import SentenceTransformer, CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model names
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/e5-base-v2")
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")


def download_models():
    """Download and cache models in the Docker image"""
    logger.info("=" * 60)
    logger.info("Downloading models for caching in Docker image...")
    logger.info("=" * 60)
    
    # Download embedding model
    logger.info(f"\n[1/2] Downloading embedding model: {EMBEDDING_MODEL}")
    logger.info("This may take a few minutes (~400MB)...")
    embedding_model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    logger.info(f"✓ Embedding model downloaded and cached")
    logger.info(f"  Model size: ~{sum(p.numel() for p in embedding_model.parameters()) / 1e6:.1f}M parameters")
    
    # Download reranker model
    logger.info(f"\n[2/2] Downloading reranker model: {RERANKER_MODEL}")
    logger.info("This may take a few minutes (~400MB)...")
    reranker_model = CrossEncoder(RERANKER_MODEL, device="cpu")
    logger.info(f"✓ Reranker model downloaded and cached")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ All models downloaded and cached successfully!")
    logger.info("=" * 60)
    logger.info("\nModels will be quantized at runtime for:")
    logger.info("  • 75% memory reduction (1.5GB → 400MB)")
    logger.info("  • 2-3x faster inference")
    logger.info("  • Fast startup (~2-3s)")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        download_models()
        logger.info("\n✓ Model preparation complete!")
        
    except Exception as e:
        logger.error(f"\n✗ Error downloading models: {e}")
        logger.error("Build will fail. Please check your internet connection.")
        raise
