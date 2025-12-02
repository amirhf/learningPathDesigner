import logging
from qdrant_client import QdrantClient
from config import get_settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

def inspect_qdrant():
    client = QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
    )
    
    print(f"Connecting to Qdrant at {settings.qdrant_url}...")
    
    # Get collection info
    try:
        info = client.get_collection(settings.qdrant_collection)
        print(f"Collection '{settings.qdrant_collection}' status: {info.status}")
        print(f"Points count: {info.points_count}")
    except Exception as e:
        print(f"Error getting collection info: {e}")
        return

    # Scroll points
    print("\n--- Sample Points ---")
    response = client.scroll(
        collection_name=settings.qdrant_collection,
        limit=5,
        with_payload=True,
        with_vectors=False
    )
    
    points = response[0]
    for point in points:
        print(f"ID: {point.id}")
        print(f"Payload: {point.payload}")
        print("-" * 20)

if __name__ == "__main__":
    inspect_qdrant()
