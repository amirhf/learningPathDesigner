"""
RAG Service - FastAPI application
Handles embeddings, search, and reranking
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.port)
