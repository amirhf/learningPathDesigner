"""
Resource ingestion pipeline
Embeds resources and stores them in Qdrant and PostgreSQL
"""
import json
import os
import sys
import uuid
from pathlib import Path
from typing import List, Dict, Any

import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer

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


def get_db_connection():
    """Get database connection"""
    database_url = os.getenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/learnpath"
    )
    return psycopg2.connect(database_url)


def get_qdrant_client():
    """Get Qdrant client"""
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    return QdrantClient(url=qdrant_url, api_key=qdrant_api_key)


def load_embedding_model():
    """Load the embedding model"""
    model_name = os.getenv("E5_MODEL_NAME", "intfloat/e5-base-v2")
    print(f"Loading embedding model: {model_name}...")
    model = SentenceTransformer(model_name)
    print("[OK] Model loaded")
    return model


def get_skill_id_map(conn) -> Dict[str, str]:
    """Get mapping of skill slugs to UUIDs"""
    cur = conn.cursor()
    cur.execute("SELECT id, slug FROM skill")
    skill_map = {slug: str(skill_id) for skill_id, slug in cur.fetchall()}
    cur.close()
    return skill_map


def resolve_skill_ids(skill_slugs: List[str], skill_map: Dict[str, str]) -> List[str]:
    """Convert skill slugs to UUIDs"""
    skill_ids = []
    for slug in skill_slugs:
        if slug in skill_map:
            skill_ids.append(skill_map[slug])
        else:
            print(f"  [WARN] Skill slug '{slug}' not found in database")
    return skill_ids


def insert_resource(conn, resource: Dict[str, Any], skill_ids: List[str]) -> str:
    """Insert resource into PostgreSQL and return UUID"""
    cur = conn.cursor()
    
    # Generate UUID
    resource_id = str(uuid.uuid4())
    
    # Insert resource
    cur.execute(
        """
        INSERT INTO resource (
            id, title, url, provider, license, duration_min, 
            level, skills, media_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::uuid[], %s)
        ON CONFLICT (url) DO UPDATE
        SET title = EXCLUDED.title,
            provider = EXCLUDED.provider,
            license = EXCLUDED.license,
            duration_min = EXCLUDED.duration_min,
            level = EXCLUDED.level,
            skills = EXCLUDED.skills,
            media_type = EXCLUDED.media_type
        RETURNING id
        """,
        (
            resource_id,
            resource["title"],
            resource["url"],
            resource.get("provider"),
            resource.get("license"),
            resource.get("duration_min"),
            resource.get("level"),
            skill_ids,
            resource.get("media_type")
        )
    )
    
    result = cur.fetchone()
    if result:
        resource_id = str(result[0])
    
    conn.commit()
    cur.close()
    
    return resource_id


def generate_embedding(model: SentenceTransformer, resource: Dict[str, Any]) -> List[float]:
    """Generate embedding for a resource"""
    # Combine title and description for embedding
    text = resource["title"]
    if resource.get("description"):
        text += " " + resource["description"]
    
    # Add passage prefix for e5 model
    prefixed_text = f"passage: {text}"
    
    # Generate embedding
    embedding = model.encode(prefixed_text, convert_to_numpy=True)
    return embedding.tolist()


def upsert_to_qdrant(
    client: QdrantClient,
    resource_id: str,
    embedding: List[float],
    resource: Dict[str, Any]
):
    """Upsert resource to Qdrant"""
    collection_name = os.getenv("QDRANT_COLLECTION", "resources")
    
    # Prepare payload
    payload = {
        "resource_id": resource_id,
        "title": resource["title"],
        "url": resource["url"],
        "provider": resource.get("provider"),
        "license": resource.get("license"),
        "duration_min": resource.get("duration_min"),
        "level": resource.get("level"),
        "skills": resource.get("skills", []),
        "media_type": resource.get("media_type"),
        "description": resource.get("description")
    }
    
    # Create point
    point = PointStruct(
        id=resource_id,
        vector=embedding,
        payload=payload
    )
    
    # Upsert
    client.upsert(
        collection_name=collection_name,
        points=[point]
    )


def ingest_resources(resources: List[Dict[str, Any]], limit: int = None):
    """Ingest resources into PostgreSQL and Qdrant"""
    load_env()
    
    # Limit resources if specified
    if limit:
        resources = resources[:limit]
    
    print(f"Ingesting {len(resources)} resources...")
    print()
    
    # Connect to services
    print("Connecting to services...")
    conn = get_db_connection()
    qdrant_client = get_qdrant_client()
    
    # Load embedding model
    embedding_model = load_embedding_model()
    
    # Get skill mapping
    skill_map = get_skill_id_map(conn)
    print(f"[OK] Loaded {len(skill_map)} skills from database")
    print()
    
    # Process each resource
    success_count = 0
    error_count = 0
    
    for i, resource in enumerate(resources, 1):
        try:
            print(f"[{i}/{len(resources)}] Processing: {resource['title']}")
            
            # Resolve skill IDs
            skill_slugs = resource.get("skills", [])
            skill_ids = resolve_skill_ids(skill_slugs, skill_map)
            
            # Insert into PostgreSQL
            resource_id = insert_resource(conn, resource, skill_ids)
            print(f"  [OK] Inserted into PostgreSQL (ID: {resource_id[:8]}...)")
            
            # Generate embedding
            embedding = generate_embedding(embedding_model, resource)
            print(f"  [OK] Generated embedding ({len(embedding)} dims)")
            
            # Upsert to Qdrant
            upsert_to_qdrant(qdrant_client, resource_id, embedding, resource)
            print(f"  [OK] Upserted to Qdrant")
            
            success_count += 1
            print()
            
        except Exception as e:
            print(f"  [ERROR] Failed to process resource: {e}")
            error_count += 1
            print()
    
    # Close connections
    conn.close()
    
    # Summary
    print("=" * 50)
    print(f"Ingestion complete!")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(resources)}")
    print("=" * 50)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest resources into the system")
    parser.add_argument(
        "--seed",
        type=str,
        help="Path to seed resources JSON file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of resources to ingest"
    )
    
    args = parser.parse_args()
    
    # Load resources
    if args.seed:
        seed_file = Path(args.seed)
        if not seed_file.exists():
            print(f"[ERROR] Seed file not found: {seed_file}")
            sys.exit(1)
        
        with open(seed_file) as f:
            resources = json.load(f)
    else:
        print("[ERROR] Please provide --seed argument with path to resources JSON")
        sys.exit(1)
    
    # Ingest resources
    try:
        ingest_resources(resources, limit=args.limit)
    except Exception as e:
        print(f"\n[ERROR] Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
