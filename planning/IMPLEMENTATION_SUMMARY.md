# Implementation Plan Summary

## Documents Overview

This planning directory contains three key documents:

### 1. **design.md** - Detailed Technical Design
- Complete architecture specification
- Data models (Postgres DDL, Qdrant schema)
- API contracts (OpenAPI sketches)
- Prompt templates and JSON schemas
- AWS deployment topology (ECS, RDS, ALB, etc.)
- 4-week phase-by-phase plan
- Initial seed resource list (60 URLs)

### 2. **plan.md** - MVP Strategy
- High-level architecture decisions
- Tech stack justification (Go gateway, FastAPI services, e5-base embeddings)
- Minimal data model
- Agent orchestration pattern (lightweight JSON-tool style)
- 4-week milestone breakdown
- Demo script for portfolio reviewers

### 3. **lean_deployment_plan.md** - Rapid Deployment Strategy
- Managed platform approach (Railway, Vercel, Supabase)
- 60-90 minute initial deployment target
- No Terraform required for MVP
- Environment variable matrix
- Migration path to AWS preserved

### 4. **implementation_steps.md** - Actionable Checklist
- Step-by-step breakdown of all 5 phases
- Time estimates for each task
- Concrete deliverables per phase
- Technology versions and deployment instructions

---

## Recommended Implementation Approach

### Strategy: Lean First, AWS Later

**Phase 0-3 (Days 1-12):** Use managed platforms
- Deploy to Railway + Vercel for speed
- Use Qdrant Cloud, Neon Postgres, Supabase Auth
- Focus on core features: search, plan generation, quizzes

**Phase 4-5 (Days 13-18):** Polish and launch
- Add authentication and observability
- Production hardening
- Public launch

**Post-MVP:** Migrate to AWS
- Follow design.md for full AWS architecture
- Use Terraform from /iac directory
- Maintain API compatibility

---

## Key Features

### Core Functionality
1. **RAG-Powered Search**
   - e5-base embeddings (768 dims)
   - Qdrant vector search with filters
   - bge-reranker-base for top-k refinement

2. **AI Plan Generation**
   - LLM agent with tool calling (OpenRouter)
   - Skill graph with prerequisites
   - Time-budget aware sequencing

3. **Grounded Quizzes**
   - Auto-generated from resource snippets
   - 100% citation requirement
   - MCQ + short answer formats

4. **Adaptive Replanning**
   - Progress tracking
   - Schedule compression when behind
   - Resource swapping (long → short)

5. **Shareable Plans**
   - Public read-only links
   - Portfolio-ready demo

---

## Architecture Diagram

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTPS
┌──────▼──────────┐
│  Next.js (Vercel)│
└──────┬──────────┘
       │ API calls
┌──────▼──────────┐
│ Go Gateway      │ ← JWT verification
│  (Railway)      │ ← Rate limiting
└──────┬──────────┘
       │
   ┌───┴───┬───────┬─────────┐
   │       │       │         │
┌──▼──┐ ┌─▼──┐ ┌──▼───┐  ┌─▼────┐
│ RAG │ │Plan│ │ Quiz │  │Worker│
│Svc  │ │Svc │ │ Svc  │  │      │
└──┬──┘ └─┬──┘ └──┬───┘  └──────┘
   │      │       │
   └──────┼───────┘
          │
   ┌──────┼────────┬─────────┐
   │      │        │         │
┌──▼──┐ ┌▼───┐ ┌──▼──────┐ ┌▼──┐
│Qdrant│ │PG  │ │Supabase │ │S3 │
│Cloud │ │Neon│ │ Storage │ │   │
└──────┘ └────┘ └─────────┘ └───┘
```

---

## Technology Stack

### Frontend
- **Next.js 14** (App Router, TypeScript)
- **Tailwind CSS** + **shadcn/ui** components
- **TanStack Query** for data fetching
- **Lucide** icons

### Backend Services
- **Go 1.21+** (Gin framework) - Gateway
- **Python 3.11** (FastAPI) - AI services
- **OpenRouter** - LLM generation
- **HuggingFace Transformers** - Embeddings

### Data Layer
- **Qdrant Cloud** - Vector search
- **Neon/Supabase** - Postgres
- **Supabase Storage** - Object storage

### Infrastructure
- **Railway** - Container hosting
- **Vercel** - Frontend hosting
- **GitHub Actions** - CI/CD

---

## Quick Start

### 1. Clone and Setup
```bash
git clone <repo>
cd learnPathDesigner
cp .env.example .env.local
docker-compose up -d
```

### 2. Run Migrations
```bash
./ops/migrate.sh
python -m ingestion.seed_skills
```

### 3. Ingest Resources
```bash
python -m ingestion.ingest --seed seed_resources.json
```

### 4. Start Services Locally
```bash
# Terminal 1: RAG service
cd services/rag
uvicorn main:app --reload

# Terminal 2: Planner service
cd services/planner
uvicorn main:app --reload --port 8001

# Terminal 3: Quiz service
cd services/quiz
uvicorn main:app --reload --port 8002

# Terminal 4: Gateway
cd gateway
go run main.go

# Terminal 5: Frontend
cd frontend
npm run dev
```

### 5. Deploy to Production
```bash
# Push to main branch
git push origin main

# Railway and Vercel auto-deploy via GitHub integration
```

---

## Success Metrics

### Technical Performance
- Search latency: <500ms (p95)
- Plan generation: <30s (p95)
- Quiz generation: <10s (p95)
- Uptime: 99.5%+

### Quality Metrics
- Resource relevance: 90%+ match skill level
- Quiz grounding: 100% cited
- Prerequisite preservation: 100%

### Cost Targets
- MVP: <$50/month total
- OpenRouter: <$20/month (100 plans)

---

## Demo Script (5 minutes)

1. **Login** (30s)
   - Sign up with email
   - Verify and login

2. **Create Goal** (1m)
   - Title: "Event-driven microservices interview prep"
   - Duration: 4 weeks
   - Time: 6 hours/week
   - Level: Intermediate

3. **View Plan** (1m)
   - See 4 weeks with 3-4 lessons each
   - Click resource chips
   - Note citations and time estimates

4. **Take Quiz** (2m)
   - Open a lesson
   - Click "Take Quiz"
   - Answer 2-4 questions
   - See score and explanations

5. **Replan** (30s)
   - Mark a lesson as "skipped"
   - Click "Replan"
   - See compressed schedule

6. **Share** (30s)
   - Click "Share Plan"
   - Copy public link
   - Open in incognito (read-only view)

---

## Next Steps

### Immediate (Day 1)
1. Review all planning documents
2. Set up platform accounts (Railway, Vercel, etc.)
3. Create GitHub repository
4. Initialize local dev environment

### Week 1
- Complete Phase 0 (Foundation)
- Complete Phase 1 (RAG & Search)
- Deploy first working feature

### Week 2
- Complete Phase 2 (Plan Generation)
- Deploy end-to-end planning flow

### Week 3
- Complete Phase 3 (Quizzes & Progress)
- Complete Phase 4 (Auth & Polish)

### Week 4
- Complete Phase 5 (Launch)
- Record demo video
- Public announcement

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM cost spike | Cache summaries, cap context length |
| Qdrant performance | Use managed cloud, monitor latency |
| Licensing issues | Curate seed list, link-only for proprietary |
| Cold start latency | Keep services warm with health checks |
| Platform limits | Start with free tiers, upgrade as needed |

---

## Support & Resources

- **Design Reference:** design.md (full AWS architecture)
- **MVP Strategy:** plan.md (tech decisions)
- **Deployment Guide:** lean_deployment_plan.md (managed platforms)
- **Task Checklist:** implementation_steps.md (actionable steps)

---

## Questions to Resolve

Before starting implementation:
1. Which Postgres provider? (Neon vs Supabase)
2. Which auth provider? (Supabase Auth vs Clerk)
3. Domain name for deployment?
4. OpenRouter model preference? (Claude 3.5 Sonnet vs GPT-4)
5. Budget allocation? (Total monthly spend limit)

---

**Ready to start? Begin with Phase 0 in implementation_steps.md**
