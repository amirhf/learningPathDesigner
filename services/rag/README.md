# RAG Service

Retrieval-Augmented Generation service for semantic search over learning resources.

## Features

- **Embeddings**: e5-base-v2 (768-dim) for semantic search
- **Reranking**: bge-reranker-base cross-encoder for improved relevance
- **Vector Search**: Qdrant for fast similarity search
- **Filtering**: Level, duration, media type, provider filters
- **Quantization**: INT8 quantization for 75% memory reduction and 2-3x speedup (see [QUANTIZATION.md](./QUANTIZATION.md))

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Preload Models (Recommended)

Download models before first run to avoid delays:

```bash
python preload_models.py
```

This downloads ~1.1GB of models and caches them locally.

### 3. Start Service

```bash
uvicorn main:app --port 8001
```

Or with auto-reload for development:

```bash
uvicorn main:app --port 8001 --reload
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Generate Embeddings
```bash
POST /embed
{
  "texts": ["text to embed"],
  "instruction": "passage"  # or "query"
}
```

### Search Resources
```bash
POST /search
{
  "query": "How to implement event sourcing?",
  "top_k": 20,
  "rerank": true,
  "rerank_top_n": 5,
  "filters": {
    "level": 1,
    "max_duration_min": 60,
    "media_type": "video"
  }
}
```

### Rerank Documents
```bash
POST /rerank
{
  "query": "event sourcing",
  "documents": [...],
  "top_n": 5
}
```

## Configuration

Set environment variables in `.env.local`:

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/learnpath

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION=resources

# Models
E5_MODEL_NAME=intfloat/e5-base-v2
RERANKER_MODEL=BAAI/bge-reranker-base
```

## Model Caching

Models are cached in `~/.cache/huggingface/hub/` after first download.

**First run**: ~2 minutes (downloads 1.1GB)  
**Subsequent runs**: ~10 seconds (loads from cache)

### Preload for Production

In Docker or production environments, preload models during build:

```dockerfile
RUN python preload_models.py
```

This ensures models are cached in the image and startup is fast.

## Performance

- **Embedding generation**: ~50ms per text (CPU)
- **Vector search**: ~10ms for 50k vectors
- **Reranking**: ~100ms for 20 documents
- **Total search latency**: ~200-300ms

With GPU:
- **Embedding generation**: ~10ms per text
- **Reranking**: ~20ms for 20 documents

## Development

### Run Tests
```bash
pytest
```

### Format Code
```bash
black .
isort .
```

### Type Checking
```bash
mypy .
```

## Deployment

### Docker

```bash
docker build -t rag-service .
docker run -p 8001:8001 --env-file .env.local rag-service
```

### Railway

The service is configured for Railway deployment with automatic model caching.

## Troubleshooting

### NumPy Version Error

If you see "NumPy 1.x vs 2.x" errors:

```bash
pip install "numpy<2.0.0" --force-reinstall
```

### Model Download Slow

Models are downloaded from Hugging Face (~1.1GB). On slow connections:

1. Download models manually to `~/.cache/huggingface/hub/`
2. Or use a mirror: `export HF_ENDPOINT=https://hf-mirror.com`

### Out of Memory

The models require ~2GB RAM. If running out of memory:

1. Reduce batch size in `embeddings.py`
2. Use smaller models (e.g., `sentence-transformers/all-MiniLM-L6-v2`)
3. Disable reranking

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │
│   main.py   │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│ Embeddings  │  │   Search    │
│ (e5-base)   │  │  (Qdrant)   │
└─────────────┘  └─────────────┘
       │
       ▼
┌─────────────┐
│   Rerank    │
│ (bge-base)  │
└─────────────┘
```

## Resources

- [e5-base-v2 Model](https://huggingface.co/intfloat/e5-base-v2)
- [bge-reranker-base](https://huggingface.co/BAAI/bge-reranker-base)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
