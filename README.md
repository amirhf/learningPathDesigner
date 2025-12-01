# Learning Path Designer – Agentic Workflow Orchestrator

**Structured RAG + Planner–Executor agents in Go + Python**

Live demo: https://learning-path-designer-git-main-amir-firouzs-projects.vercel.app

## Why this exists

This repo is a **reference architecture** for building production-ready AI agents. It demonstrates how to move beyond toy demos to a robust, distributed system featuring:

*   **Go gateway** coordinating multiple AI microservices.
*   **RAG** over domain content with Qdrant + Postgres.
*   **Deterministic planner & quiz generator** using structured outputs.
*   **Ready to adapt** to any domain: onboarding, internal training, certification prep.

## Agent Patterns Implemented

*   **Planner–Executor**: Planner proposes a path; executor decomposes into concrete steps with resources.
*   **RAG + Re-ranking pipeline**: Semantic search (e5-base) → Reranking (bge-reranker) → Context window construction.
*   **Structured JSON outputs**: All plans & quizzes are strictly validated against schemas.
*   **Multi-service Orchestration**: Frontend (Next.js) → Go Gateway → Python AI microservices → Qdrant + Postgres.

## Reference Architecture

This project is designed to be forked and adapted. It serves as a blueprint for:

*   **Internal L&D Teams:** Create personalized onboarding paths from your internal wikis and PDFs.
*   **EdTech Startups:** Build adaptive learning platforms with grounded assessments.
*   **AI Engineers:** See a working example of Go-based agent orchestration handling Python ML services.

## Architecture

```
Frontend (Next.js) → Gateway (Go) → AI Services (FastAPI)
                                    ├─ RAG Service
                                    ├─ Planner Service
                                    └─ Quiz Service
                                    
Data Layer: Qdrant (vectors) + Postgres (metadata) + S3 (snippets)
```

## Tech Stack

- **Frontend:** Next.js 14, TypeScript, Tailwind CSS, shadcn/ui
- **Gateway:** Go 1.21+, Gin framework
- **AI Services:** Python 3.11, FastAPI
- **Embeddings:** e5-base-v2 (768 dims)
- **Reranker:** bge-reranker-base
- **LLM:** OpenRouter (Claude/GPT-4)
- **Vector DB:** Qdrant Cloud
- **Database:** PostgreSQL (Neon/Supabase)
- **Auth:** Supabase Auth
- **Deployment:** Railway + Vercel

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Go 1.21+
- Node.js 20+

### Local Development

1. **Clone and setup:**
   ```powershell
   git clone <repo-url>
   cd learnPathDesigner
   
   # Run automated setup (Windows)
   .\setup.ps1
   
   # Or manually:
   cp .env.example .env.local
   python -m venv .venv
   ```

2. **Activate virtual environment:**
   ```powershell
   # Windows
   .\.venv\Scripts\Activate.ps1
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```powershell
   pip install -r ingestion/requirements.txt
   pip install -r services/rag/requirements.txt
   ```

4. **Start infrastructure:**
   ```powershell
   docker-compose up -d
   ```

5. **Run migrations:**
   ```powershell
   # Windows (with psql installed)
   .\ops\migrate.ps1
   
   # Or via Docker
   Get-Content shared/migrations/001_initial_schema.sql | docker exec -i learnpath-postgres psql -U postgres -d learnpath
   ```

6. **Seed data:**
   ```powershell
   python -m ingestion.seed_skills
   python -m ingestion.setup_qdrant
   python -m ingestion.ingest --seed ingestion/seed_resources.json --limit 50
   ```

7. **Start services:**
   ```powershell
   # Terminal 1: RAG service
   cd services/rag
   uvicorn main:app --reload --port 8001

   # Terminal 2: Planner service
   cd services/planner
   uvicorn main:app --reload --port 8002

   # Terminal 3: Quiz service
   cd services/quiz
   uvicorn main:app --reload --port 8003

   # Terminal 4: Gateway
   cd gateway
   go run main.go

   # Terminal 5: Frontend
   cd frontend
   npm install
   npm run dev
   ```
   
   **Note:** Make sure your virtual environment is activated in each terminal before running Python services.

6. **Access:**
   - Frontend: http://localhost:3000
   - Gateway: http://localhost:8080
   - RAG Service: http://localhost:8001
   - Planner Service: http://localhost:8002
   - Quiz Service: http://localhost:8003

## Project Structure

```
/frontend              # Next.js application
/gateway               # Go API gateway
/services/
  /rag                 # RAG service (embeddings, search, rerank)
  /planner             # Planner service (plan generation, replanning)
  /quiz                # Quiz service (generation, grading)
/ingestion             # Data ingestion scripts
/shared/
  /migrations          # Database migrations
  /schemas             # Shared data schemas
/ops                   # Docker files, scripts
/.github/workflows     # CI/CD pipelines
```

## Environment Variables

See `.env.example` for all required variables.

Key variables:
- `DATABASE_URL` - Postgres connection string
- `QDRANT_URL` - Qdrant Cloud URL
- `QDRANT_API_KEY` - Qdrant API key
- `OPENROUTER_API_KEY` - OpenRouter API key
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key

## Deployment

### Railway (Backend Services)

1. Connect GitHub repository
2. Create services for: gateway, rag, planner, quiz
3. Set environment variables
4. Deploy

### Vercel (Frontend)

1. Connect GitHub repository
2. Set root directory to `/frontend`
3. Set environment variables
4. Deploy

## Documentation

- [Implementation Plan](planning/implementation_steps.md)
- [Design Document](planning/design.md)
- [Lean Deployment Guide](planning/lean_deployment_plan.md)

## License

MIT
