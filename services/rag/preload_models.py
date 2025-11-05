"""
Preload models for RAG service
Run this script to download and cache models before deployment
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sentence_transformers import SentenceTransformer, CrossEncoder


def preload_models():
    """Download and cache all required models"""
    print("=" * 60)
    print("Preloading RAG Service Models")
    print("=" * 60)
    print()
    
    # Model names
    embedding_model = os.getenv("E5_MODEL_NAME", "intfloat/e5-base-v2")
    reranker_model = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
    
    # Download embedding model
    print(f"1. Downloading embedding model: {embedding_model}")
    print("-" * 60)
    try:
        model = SentenceTransformer(embedding_model)
        print(f"✓ Embedding model loaded successfully")
        print(f"  Model size: {model.get_sentence_embedding_dimension()} dimensions")
        print()
    except Exception as e:
        print(f"✗ Failed to load embedding model: {e}")
        sys.exit(1)
    
    # Download reranker model
    print(f"2. Downloading reranker model: {reranker_model}")
    print("-" * 60)
    try:
        reranker = CrossEncoder(reranker_model)
        print(f"✓ Reranker model loaded successfully")
        print()
    except Exception as e:
        print(f"✗ Failed to load reranker model: {e}")
        sys.exit(1)
    
    print("=" * 60)
    print("All models preloaded successfully!")
    print("=" * 60)
    print()
    print("Models are cached in:")
    cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
    print(f"  {cache_dir}")
    print()
    print("The RAG service will now start faster on subsequent runs.")


if __name__ == "__main__":
    preload_models()
