"""
Setup Qdrant collection for resources
"""
import os
import sys
from pathlib import Path

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_env():
    """Load environment variables from .env.local"""
    env_file = Path(__file__).parent.parent / ".env.local"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    os.environ[key] = value


def setup_collection():
    """Create Qdrant collection and indexes"""
    load_env()
    
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    collection_name = "resources"
    
    print(f"Connecting to Qdrant at {qdrant_url}...")
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    # Check if collection exists
    collections = client.get_collections().collections
    collection_exists = any(c.name == collection_name for c in collections)
    
    if collection_exists:
        print(f"Collection '{collection_name}' already exists")
        response = input("Do you want to recreate it? (yes/no): ")
        if response.lower() == "yes":
            print(f"Deleting collection '{collection_name}'...")
            client.delete_collection(collection_name)
        else:
            print("Keeping existing collection")
            return
    
    # Create collection
    print(f"Creating collection '{collection_name}'...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=768,  # e5-base-v2 dimension
            distance=Distance.COSINE
        )
    )
    print("[OK] Collection created")
    
    # Create payload indexes for filtering
    print("Creating payload indexes...")
    
    # Index for level (integer)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="level",
        field_schema=PayloadSchemaType.INTEGER
    )
    print("  [OK] Index on 'level'")
    
    # Index for duration_min (integer)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="duration_min",
        field_schema=PayloadSchemaType.INTEGER
    )
    print("  [OK] Index on 'duration_min'")
    
    # Index for media_type (keyword)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="media_type",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("  [OK] Index on 'media_type'")
    
    # Index for provider (keyword)
    client.create_payload_index(
        collection_name=collection_name,
        field_name="provider",
        field_schema=PayloadSchemaType.KEYWORD
    )
    print("  [OK] Index on 'provider'")
    
    # Get collection info
    collection_info = client.get_collection(collection_name)
    print(f"\n[OK] Collection setup complete!")
    print(f"  Name: {collection_name}")
    print(f"  Vector size: {collection_info.config.params.vectors.size}")
    print(f"  Distance: {collection_info.config.params.vectors.distance}")
    print(f"  Points count: {collection_info.points_count}")


def main():
    """Main entry point"""
    try:
        setup_collection()
    except Exception as e:
        print(f"\n[ERROR] Failed to setup collection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
