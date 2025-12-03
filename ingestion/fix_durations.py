import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from bs4 import BeautifulSoup
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

# Configuration (from env or defaults)
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/learnpath")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "resources")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

def extract_duration(url):
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
            
        text = soup.get_text()
        words = len(text.split())
        minutes = max(1, round(words / 200))
        return minutes
    except Exception as e:
        logger.error(f"Error extracting from {url}: {e}")
        return None

def main():
    conn = get_db_connection()
    qdrant = QdrantClient(url=QDRANT_URL)
    
    try:
        with conn.cursor() as cur:
            # Find resources with 0 or null duration
            cur.execute("SELECT id, url, title, duration_min, tenant_id FROM resource WHERE duration_min IS NULL OR duration_min = 0")
            resources = cur.fetchall()
            
            logger.info(f"Found {len(resources)} resources to update")
            
            for res in resources:
                res_id = res['id']
                url = res['url']
                
                logger.info(f"Processing: {res['title']} ({url})")
                
                duration = extract_duration(url)
                if duration:
                    logger.info(f"  -> Estimated duration: {duration} min")
                    
                    # Update Postgres
                    cur.execute("UPDATE resource SET duration_min = %s WHERE id = %s", (duration, res_id))
                    
                    # Update Qdrant
                    # We need to fetch existing payload first to preserve other fields?
                    # Or Qdrant 'set_payload' updates specific fields.
                    qdrant.set_payload(
                        collection_name=QDRANT_COLLECTION,
                        points=[res_id],
                        payload={"duration_min": duration}
                    )
                    
                    conn.commit()
                else:
                    logger.warning("  -> Could not estimate duration")
                    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
