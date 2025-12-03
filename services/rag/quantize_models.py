"""
Download and cache models during Docker build for faster startup
Quantization is applied at runtime (still fast, ~2-3s)
"""
import logging
import os
import time
import shutil
from sentence_transformers import SentenceTransformer, CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model names
EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL", "intfloat/e5-base-v2")
RERANKER_MODEL_ID = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")

# Local cache paths (from Cloud Build fetch step)
CACHE_BASE = "/app/models_cache"
EMBEDDING_CACHE = f"{CACHE_BASE}/embedding"
RERANKER_CACHE = f"{CACHE_BASE}/reranker"

# Runtime model paths (where we will save/verify them)
RUNTIME_MODELS_DIR = "/app/models"
RUNTIME_EMBEDDING = f"{RUNTIME_MODELS_DIR}/embedding"
RUNTIME_RERANKER = f"{RUNTIME_MODELS_DIR}/reranker"


def retry_with_backoff(func, retries=5, backoff_in_seconds=10):
    """Retry a function with exponential backoff"""
    x = 0
    while True:
        try:
            return func()
        except Exception as e:
            if x == retries:
                raise
            sleep = (backoff_in_seconds * 2 ** x)
            logger.warning(f"Error: {e}. Retrying in {sleep}s...")
            time.sleep(sleep)
            x += 1


def download_models():
    """Download and cache models in the Docker image"""
    logger.info("=" * 60)
    logger.info("Preparing models for Docker image...")
    logger.info("=" * 60)
    
    os.makedirs(RUNTIME_MODELS_DIR, exist_ok=True)
    
    # --- Embedding Model ---
    logger.info(f"\n[1/2] Processing embedding model: {EMBEDDING_MODEL_ID}")
    if os.path.exists(EMBEDDING_CACHE):
        logger.info(f"Found local cache at {EMBEDDING_CACHE}. Loading...")
        embedding_model = SentenceTransformer(EMBEDDING_CACHE, device="cpu")
    else:
        logger.info(f"No local cache. Downloading from Hugging Face (with retry)...")
        def download_embedding():
            return SentenceTransformer(EMBEDDING_MODEL_ID, device="cpu")
        embedding_model = retry_with_backoff(download_embedding)
    
    logger.info(f"Saving embedding model to runtime path: {RUNTIME_EMBEDDING}")
    embedding_model.save(RUNTIME_EMBEDDING)
    logger.info(f"✓ Embedding model ready")

    # --- Reranker Model ---
    logger.info(f"\n[2/2] Processing reranker model: {RERANKER_MODEL_ID}")
    if os.path.exists(RERANKER_CACHE):
        logger.info(f"Found local cache at {RERANKER_CACHE}. Loading...")
        reranker_model = CrossEncoder(RERANKER_CACHE, device="cpu")
        # CrossEncoder doesn't have a simple .save() method that behaves exactly like SentenceTransformer
        # But we can save using the underlying auto_model if needed, or just use the path.
        # However, CrossEncoder.save() exists.
        logger.info(f"Saving reranker model to runtime path: {RUNTIME_RERANKER}")
        reranker_model.save(RUNTIME_RERANKER)
    else:
        logger.info(f"No local cache. Downloading from Hugging Face (with retry)...")
        def download_reranker():
            return CrossEncoder(RERANKER_MODEL_ID, device="cpu")
        reranker_model = retry_with_backoff(download_reranker)
        logger.info(f"Saving reranker model to runtime path: {RUNTIME_RERANKER}")
        reranker_model.save(RUNTIME_RERANKER)

    logger.info(f"✓ Reranker model ready")
    
    logger.info("\n" + "=" * 60)
    logger.info("✓ All models prepared successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    try:
        download_models()
        logger.info("\n✓ Model preparation complete!")
        
    except Exception as e:
        logger.error(f"\n✗ Error downloading models: {e}")
        logger.error("Build will fail. Please check your internet connection.")
        raise
