"""
RAG (Retrieval-Augmented Generation) Service
Handles semantic search over learning resources using Qdrant
Also provides ingestion endpoints for skills and resources
"""
import logging
import os
import uuid
import boto3
import requests
from bs4 import BeautifulSoup
from contextlib import asynccontextmanager
from typing import List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import get_settings
from models import (
    EmbedRequest, EmbedResponse,
    SearchRequest, SearchResponse, ResourceResult,
    RerankRequest, RerankResponse,
    HealthResponse
)
from embeddings import get_embedding_service
from search import get_search_service
from rerank import get_rerank_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info(f"Starting {settings.service_name} on port {settings.port}")
    logger.info(f"Environment: {settings.environment}")
    
    # NOTE: Models and Qdrant connection are loaded lazily on first request
    # This ensures fast startup for Cloud Run health checks
    logger.info("Service will load models and connect to Qdrant on first request")
    logger.info("Service ready")
    
    yield
    
    # Shutdown
    logger.info("Shutting down service")


# Create FastAPI app
app = FastAPI(
    title="RAG Service",
    description="Retrieval-Augmented Generation service for Learning Path Designer",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    logger.info("Health check called")
    
    # Check if services are initialized (lazy loading)
    models_loaded = False
    qdrant_connected = False
    
    try:
        # Try to get embedding service to check if models are loaded
        embedding_service = get_embedding_service()
        models_loaded = embedding_service is not None
    except Exception:
        pass
    
    try:
        # Try to get search service to check Qdrant connection
        search_service = get_search_service()
        qdrant_connected = search_service is not None
    except Exception:
        pass
    
    return HealthResponse(
        status="healthy",
        service=settings.service_name,
        qdrant_connected=qdrant_connected,
        models_loaded=models_loaded
    )


@app.post("/embed", response_model=EmbedResponse)
async def generate_embeddings(request: EmbedRequest):
    """
    Generate embeddings for a list of texts
    """
    try:
        embedding_service = get_embedding_service()
        embeddings = embedding_service.generate_embeddings(
            request.texts,
            instruction=request.instruction
        )
        
        return EmbedResponse(
            embeddings=embeddings,
            dimension=settings.embedding_dimension,
            model=settings.embedding_model
        )
    
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_resources(request: SearchRequest):
    """
    Search for learning resources using semantic search
    """
    try:
        search_service = get_search_service()
        
        # Convert filters to dict
        filters_dict = request.filters.model_dump() if request.filters else None
        
        # Perform search
        results = search_service.search(
            query=request.query,
            filters=filters_dict,
            top_k=request.top_k
        )
        
        # Apply reranking if requested
        if request.rerank and len(results) > 0:
            rerank_service = get_rerank_service()
            reranked_results, scores = rerank_service.rerank(
                query=request.query,
                documents=results,
                top_n=min(request.rerank_top_n, len(results))
            )
            
            # Update scores
            for i, result in enumerate(reranked_results):
                result["score"] = scores[i]
            
            results = reranked_results
            reranked = True
        else:
            reranked = False
        
        # Convert to response model
        resource_results = [
            ResourceResult(**result) for result in results
        ]
        
        return SearchResponse(
            results=resource_results,
            query=request.query,
            total_found=len(resource_results),
            reranked=reranked
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    Rerank a list of documents based on relevance to query
    """
    try:
        rerank_service = get_rerank_service()
        
        reranked_docs, scores = rerank_service.rerank(
            query=request.query,
            documents=request.documents,
            top_n=request.top_n
        )
        
        return RerankResponse(
            results=reranked_docs,
            scores=scores
        )
    
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": settings.service_name,
        "version": "1.0.0",
        "status": "running"
    }


# ============================================================================
# INGESTION ENDPOINTS
# ============================================================================

# Ingestion Models
class Skill(BaseModel):
    name: str
    slug: str
    level_hint: int = Field(0, ge=0, le=2)
    description: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)


class Resource(BaseModel):
    title: str
    url: str
    provider: Optional[str] = None
    license: Optional[str] = None
    duration_min: Optional[int] = None
    level: Optional[int] = Field(None, ge=0, le=2)
    skills: List[str] = Field(default_factory=list)
    media_type: Optional[str] = None
    description: Optional[str] = None


class IngestSkillsRequest(BaseModel):
    skills: List[Skill]


class IngestResourcesRequest(BaseModel):
    resources: List[Resource]
    generate_embeddings: bool = Field(True, description="Generate embeddings and store in Qdrant")
    extract_content: bool = Field(True, description="Extract content snippets from URLs and upload to S3")


class IngestResponse(BaseModel):
    success: int
    failed: int
    total: int
    errors: List[str] = Field(default_factory=list)


def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(settings.database_url, cursor_factory=RealDictCursor)


def extract_content_from_url(url: str, max_length: int = 3000) -> Optional[str]:
    """Extract text content from a URL"""
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
            element.decompose()
        
        # Try to find main content
        content = None
        for tag in [soup.find('article'), soup.find('main'), soup.find('div', class_='content')]:
            if tag:
                content = tag.get_text()
                break
        
        if not content:
            content = soup.get_text()
        
        # Clean and truncate
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        text = ' '.join(lines)
        
        if len(text) > max_length:
            text = text[:max_length]
        
        return text if len(text) > 100 else None
        
    except Exception as e:
        logger.warning(f"Failed to extract content from {url}: {e}")
        return None


def upload_to_s3(content: str, resource_id: str) -> Optional[str]:
    """Upload content snippet to S3 and return the key"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        bucket_name = os.getenv('S3_BUCKET_NAME', 'learnpath-snippets')
        s3_key = f"snippets/{resource_id}.txt"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=content.encode('utf-8'),
            ContentType='text/plain'
        )
        
        logger.info(f"Uploaded content to S3: {s3_key}")
        return s3_key
        
    except Exception as e:
        logger.error(f"Failed to upload to S3: {e}")
        return None


@app.post("/ingest/skills", response_model=IngestResponse)
async def ingest_skills(request: IngestSkillsRequest):
    """
    Ingest skills into the database
    """
    conn = get_db_connection()
    success_count = 0
    failed_count = 0
    errors = []
    
    try:
        with conn.cursor() as cur:
            # Create a map of existing skills
            cur.execute("SELECT id, slug FROM skill")
            existing_skills = {slug: str(skill_id) for skill_id, slug in cur.fetchall()}
            
            for skill in request.skills:
                try:
                    skill_id = str(uuid.uuid4())
                    
                    # Insert or update skill
                    cur.execute("""
                        INSERT INTO skill (id, name, slug, level_hint, description)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (slug) DO UPDATE
                        SET name = EXCLUDED.name,
                            level_hint = EXCLUDED.level_hint,
                            description = EXCLUDED.description,
                            updated_at = NOW()
                        RETURNING id
                    """, (skill_id, skill.name, skill.slug, skill.level_hint, skill.description))
                    
                    result = cur.fetchone()
                    if result:
                        skill_id = str(result['id'])
                    
                    existing_skills[skill.slug] = skill_id
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Failed to insert skill {skill.slug}: {str(e)}")
                    logger.error(f"Failed to insert skill {skill.slug}: {e}")
            
            # Insert prerequisite relationships
            for skill in request.skills:
                if skill.prerequisites:
                    skill_id = existing_skills.get(skill.slug)
                    if not skill_id:
                        continue
                    
                    for prereq_slug in skill.prerequisites:
                        prereq_id = existing_skills.get(prereq_slug)
                        if prereq_id:
                            try:
                                cur.execute("""
                                    INSERT INTO skill_edge (from_skill, to_skill)
                                    VALUES (%s, %s)
                                    ON CONFLICT DO NOTHING
                                """, (prereq_id, skill_id))
                            except Exception as e:
                                logger.warning(f"Failed to insert prerequisite edge: {e}")
            
            conn.commit()
            
    except Exception as e:
        conn.rollback()
        logger.error(f"Transaction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        conn.close()
    
    return IngestResponse(
        success=success_count,
        failed=failed_count,
        total=len(request.skills),
        errors=errors
    )


@app.post("/ingest/resources", response_model=IngestResponse)
async def ingest_resources(request: IngestResourcesRequest):
    """
    Ingest resources into the database and optionally generate embeddings
    """
    try:
        conn = get_db_connection()
        logger.info(f"Database connection established for ingesting {len(request.resources)} resources")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    
    success_count = 0
    failed_count = 0
    errors = []
    
    try:
        with conn.cursor() as cur:
            # Get skill mapping
            cur.execute("SELECT id, slug FROM skill")
            skill_map = {slug: str(skill_id) for skill_id, slug in cur.fetchall()}
            
            for resource in request.resources:
                try:
                    resource_id = str(uuid.uuid4())
                    
                    # Resolve skill IDs
                    skill_ids = []
                    for slug in resource.skills:
                        if slug in skill_map:
                            skill_ids.append(skill_map[slug])
                        else:
                            logger.warning(f"Skill slug '{slug}' not found for resource {resource.title}")
                    
                    # Insert resource into PostgreSQL
                    logger.info(f"Inserting resource: {resource.title} (URL: {resource.url})")
                    cur.execute("""
                        INSERT INTO resource (
                            id, title, url, provider, license, duration_min,
                            level, skills, media_type, description
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::uuid[], %s, %s)
                        ON CONFLICT (url) DO UPDATE
                        SET title = EXCLUDED.title,
                            provider = EXCLUDED.provider,
                            license = EXCLUDED.license,
                            duration_min = EXCLUDED.duration_min,
                            level = EXCLUDED.level,
                            skills = EXCLUDED.skills,
                            media_type = EXCLUDED.media_type,
                            description = EXCLUDED.description,
                            updated_at = NOW()
                        RETURNING id
                    """, (
                        resource_id,
                        resource.title,
                        resource.url,
                        resource.provider,
                        resource.license,
                        resource.duration_min,
                        resource.level,
                        skill_ids,
                        resource.media_type,
                        resource.description
                    ))
                    
                    result = cur.fetchone()
                    if result:
                        resource_id = str(result['id'])
                        logger.info(f"Resource inserted/updated with ID: {resource_id}")
                    
                    # Extract content and upload to S3 if requested
                    if request.extract_content:
                        try:
                            content = extract_content_from_url(resource.url)
                            if content:
                                s3_key = upload_to_s3(content, resource_id)
                                if s3_key:
                                    # Update resource with S3 key
                                    cur.execute("""
                                        UPDATE resource
                                        SET snippet_s3_key = %s, updated_at = NOW()
                                        WHERE id = %s
                                    """, (s3_key, resource_id))
                                    logger.info(f"Extracted and uploaded content for {resource.title}")
                        except Exception as e:
                            logger.warning(f"Failed to extract content for {resource.title}: {e}")
                            # Don't fail the whole ingestion if content extraction fails
                    
                    # Generate embeddings and store in Qdrant if requested
                    if request.generate_embeddings:
                        try:
                            # Prepare text for embedding
                            text = resource.title
                            if resource.description:
                                text += f" {resource.description}"
                            
                            # Generate embedding
                            embedding_service = get_embedding_service()
                            embeddings = embedding_service.generate_embeddings([f"passage: {text}"])
                            
                            # Store in Qdrant
                            search_service = get_search_service()
                            search_service.connect()  # Ensure connection is established
                            search_service.client.upsert(
                                collection_name=settings.qdrant_collection,
                                points=[{
                                    "id": resource_id,
                                    "vector": embeddings[0],
                                    "payload": {
                                        "resource_id": resource_id,
                                        "title": resource.title,
                                        "url": resource.url,
                                        "provider": resource.provider,
                                        "license": resource.license,
                                        "duration_min": resource.duration_min,
                                        "level": resource.level,
                                        "skills": resource.skills,
                                        "media_type": resource.media_type,
                                        "description": resource.description
                                    }
                                }]
                            )
                            
                            logger.info(f"Generated embedding and stored in Qdrant for {resource.title}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to generate embedding for {resource.title}: {e}")
                            # Don't fail the whole ingestion if embedding fails
                    
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"Failed to insert resource {resource.url}: {str(e)}")
                    logger.error(f"Failed to insert resource {resource.url}: {e}")
            
            logger.info(f"Committing transaction for {success_count} resources")
            conn.commit()
            logger.info("Transaction committed successfully")
            
    except Exception as e:
        logger.error(f"Transaction failed: {e}", exc_info=True)
        try:
            conn.rollback()
            logger.info("Transaction rolled back")
        except Exception as rollback_error:
            logger.error(f"Rollback failed: {rollback_error}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    finally:
        conn.close()
    
    return IngestResponse(
        success=success_count,
        failed=failed_count,
        total=len(request.resources),
        errors=errors
    )


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.port,
        log_level="info"
    )
