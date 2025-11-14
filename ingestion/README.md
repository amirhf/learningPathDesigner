# Ingestion Scripts

This directory contains scripts for data ingestion and content extraction.

## Active Scripts (Use These)

### `ingest_via_api.py` ⭐ **RECOMMENDED**
**Purpose:** Ingest skills and resources via RAG service API  
**Usage:**
```bash
python ingestion/ingest_via_api.py \
  --api-url https://rag-service-xxx.run.app \
  --skills \
  --resources \
  --embeddings
```
**When to use:** For production ingestion. This is the sustainable approach.

### `seed_skills.py`
**Purpose:** Direct database seeding of skills (legacy, for local dev)  
**Usage:**
```bash
DATABASE_URL='postgresql://...' python ingestion/seed_skills.py
```
**When to use:** Local development or when API is not available.

### `run_content_extraction.py`
**Purpose:** Extract content from resource URLs and upload to S3  
**Usage:**
```bash
DATABASE_URL='postgresql://...' python -m ingestion.run_content_extraction
```
**When to use:** To populate `snippet_s3_key` for quiz generation. Run after resources are ingested.

## Supporting Scripts

### `ingest.py`
**Purpose:** Legacy ingestion with local embedding generation  
**Note:** Requires local ML models. Use `ingest_via_api.py` instead.

### `setup_qdrant.py`
**Purpose:** Initialize Qdrant collection  
**Usage:**
```bash
python ingestion/setup_qdrant.py
```

### `extract_content.py`
**Purpose:** Content extraction utilities (used by `run_content_extraction.py`)

### `s3_uploader.py`
**Purpose:** S3 upload utilities (used by `run_content_extraction.py`)

### `update_s3_keys.py`
**Purpose:** Database utilities for S3 key management

## Data Files

- `seed_skills.json` - 20 skills with prerequisites
- `seed_resources.json` - 49 learning resources

## Typical Workflow

### Production Deployment
1. Deploy services (RAG, Planner, Quiz, Gateway)
2. Run migrations
3. Ingest data via API:
   ```bash
   python ingestion/ingest_via_api.py \
     --api-url https://rag-service-xxx.run.app \
     --skills --resources --embeddings
   ```
4. Extract content for quizzes:
   ```bash
   DATABASE_URL='...' python -m ingestion.run_content_extraction
   ```

### Local Development
1. Start Docker services
2. Run migrations
3. Seed skills:
   ```bash
   python ingestion/seed_skills.py
   ```
4. Ingest resources via API (if RAG service is running):
   ```bash
   python ingestion/ingest_via_api.py \
     --api-url http://localhost:8001 \
     --resources --embeddings
   ```

## See Also

- `../INGESTION_GUIDE.md` - Complete ingestion documentation
- `../shared/migrations/` - Database schema migrations
