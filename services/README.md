# Services

This directory contains the microservices for the Learning Path Designer.

## Services

- **rag/** - RAG service (embeddings, search, reranking)
- **planner/** - Planner service (plan generation, replanning)
- **quiz/** - Quiz service (quiz generation, grading)

Each service is a FastAPI application with its own dependencies and Dockerfile.

## Development

Each service can be run independently:

```bash
cd services/rag
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

## Testing

```bash
cd services/rag
pytest
```
