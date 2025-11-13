# Learning Path Designer - Step-by-Step Implementation Plan

## Overview
This plan breaks down the lean deployment approach into actionable steps, organized by phase. Each phase delivers a working vertical slice.

**Timeline:** 15-18 days (part-time) or 8-10 days (full-time)
**Strategy:** Managed platforms (Railway, Vercel, Supabase) → AWS migration later

---

## PHASE 0: Foundation (Days 1-2)

### 0.1 Repository Setup (2h)
- [ ] Create GitHub repo with structure: `/frontend`, `/gateway`, `/services/*`, `/ingestion`, `/shared`, `/ops`
- [ ] Add `.gitignore`, `README.md`, root `Makefile`
- [ ] Create `docker-compose.yml` with Postgres, Qdrant, Redis

### 0.2 Platform Accounts (1h)
- [ ] Sign up: Qdrant Cloud, Neon/Supabase, Railway, Vercel, OpenRouter
- [ ] Note all API keys and URLs

### 0.3 Database Schema (3h)
- [ ] Create migrations: `skill`, `skill_edge`, `resource`, `app_user`, `goal`, `plan`, `lesson`, `progress`
- [ ] Run migrations locally
- [ ] Create seed script for 15-20 event-driven skills

**Deliverable:** Local dev environment ready, DB schema deployed

---

## PHASE 1: RAG & Search (Days 3-5)

### 1.1 RAG Service (4h)
- [ ] Create FastAPI service: `/services/rag/`
- [ ] Implement: embeddings (e5-base), search (Qdrant), rerank (bge-reranker)
- [ ] Endpoints: `POST /embed`, `POST /search`, `POST /rerank`

### 1.2 Qdrant Setup (1h)
- [ ] Create `resources` collection (768 dims, cosine)
- [ ] Add payload indexes: level, skills, duration_min

### 1.3 Seed Resources (3h)
- [ ] Create `seed_resources.json` with 50-100 curated URLs
- [ ] Include: Kafka docs, microservices.io, AWS guides, Redis docs

### 1.4 Ingestion Pipeline (4h)
- [ ] Create `/ingestion/ingest.py`: read JSON → embed → insert DB + Qdrant
- [ ] Test locally with 50 resources

### 1.5 Go Gateway (4h)
- [ ] Create Gin service: `/gateway/`
- [ ] Implement: `GET /api/resources/search`
- [ ] Add RAG service client

### 1.6 Frontend Search UI (5h)
- [ ] Next.js 14 with Tailwind + shadcn/ui
- [ ] Search page with filters (level, duration, media)
- [ ] Resource cards with badges

### 1.7 Deploy Phase 1 (3h)
- [ ] Deploy RAG service to Railway
- [ ] Deploy Gateway to Railway
- [ ] Deploy Frontend to Vercel
- [ ] Run ingestion via GitHub Action

**Deliverable:** Live search UI at Vercel URL

---

## PHASE 2: Plan Generation (Days 6-9)

### 2.1 Skill Graph (2h)
- [ ] Seed skills with prerequisites
- [ ] Create topological sort query

### 2.2 Planner Service - Tools (3h)
- [ ] Create `/services/planner/`
- [ ] Implement tools: `search_resources`, `get_skill_graph`

### 2.3 Planner Agent (5h)
- [ ] OpenRouter integration (function calling)
- [ ] System prompt + JSON schema
- [ ] Generate plan logic with LLM

### 2.4 Planner Endpoints (2h)
- [ ] `POST /plan`: create plan
- [ ] `POST /replan`: adjust plan

### 2.5 Gateway Plan Routes (3h)
- [ ] `POST /api/intake`: create goal
- [ ] `POST /api/plan`: trigger planner
- [ ] `GET /api/plan/:id`: fetch plan

### 2.6 Frontend Intake & Plan UI (6h)
- [ ] Intake form (goal, deadline, hours/week, level, prefs)
- [ ] Plan page (week cards, lesson cards, resource chips)
- [ ] Share button

### 2.7 Deploy Phase 2 (2h)
- [ ] Deploy planner-service to Railway
- [ ] Update gateway and frontend
- [ ] Test end-to-end

**Deliverable:** Users can create goals and get AI plans

---

## PHASE 3: Quizzes & Progress (Days 10-12)

### 3.1 Quiz Service (4h)
- [ ] Create `/services/quiz/`
- [ ] Implement: `generate_quiz`, `grade_quiz`
- [ ] Endpoints: `POST /generate`, `POST /grade`

### 3.2 Quiz Prompts (3h)
- [ ] Quiz generation prompt with grounding requirement
- [ ] JSON schema for quiz items (MCQ + short answer)
- [ ] Validation logic

### 3.3 Progress Tracking (2h)
- [ ] Gateway: `POST /api/progress/lesson/:id`
- [ ] Calculate completion percentage

### 3.4 Replan Logic (3h)
- [ ] Update planner with replan prompt
- [ ] Logic: compress schedule, swap resources, preserve prerequisites

### 3.5 Frontend Quiz UI (5h)
- [ ] Lesson page with quiz button
- [ ] Quiz interface (questions, submit, results)
- [ ] Progress indicators (checkmarks, progress bar)
- [ ] Replan button with diff view

### 3.6 Deploy Phase 3 (2h)
- [ ] Deploy quiz-service
- [ ] Test complete flow

**Deliverable:** Full learning loop with quizzes

---

## PHASE 4: Auth & Polish (Days 13-15)

### 4.1 Supabase Auth (2h)
- [ ] Enable email/password auth
- [ ] Create test users

### 4.2 Frontend Auth (3h)
- [ ] Install Supabase client
- [ ] Login/signup pages
- [ ] Protected routes

### 4.3 Gateway JWT (3h)
- [ ] JWT verification middleware
- [ ] Map user to app_user table

### 4.4 Observability (3h)
- [ ] Add structured logging (JSON)
- [ ] PostHog events (plan created, quiz completed)
- [ ] Sentry error tracking

### 4.5 Shareable Plans (2h)
- [ ] Generate share tokens
- [ ] Public read-only route: `/public/plan/:token`

### 4.6 UI Polish (4h)
- [ ] Responsive design
- [ ] Loading states, error handling
- [ ] Accessibility audit

### 4.7 Documentation (2h)
- [ ] Write DEMO.md
- [ ] Update README with architecture diagram
- [ ] Record demo video

**Deliverable:** Production-ready app

---

## PHASE 5: Launch (Days 16-18)

### 5.1 Testing (4h)
- [ ] Playwright E2E tests
- [ ] Load testing (10 concurrent users)

### 5.2 Content (2h)
- [ ] Ingest full 150-300 resources
- [ ] Verify search quality

### 5.3 Security (2h)
- [ ] Review IAM/permissions
- [ ] Rotate secrets
- [ ] Enable HTTPS only

### 5.4 Launch (2h)
- [ ] Custom domain setup
- [ ] Monitoring alerts
- [ ] Announce publicly

**Deliverable:** Live app ready for users

---

## Success Criteria

- [ ] Search returns relevant results in <500ms
- [ ] Plan generation completes in <30s
- [ ] Quiz questions 100% grounded in sources
- [ ] Replan preserves prerequisites
- [ ] Demo flow completes in <5 minutes
- [ ] AWS cost <$50/month

---

## Tech Stack Summary

| Layer | Technology | Deployment |
|-------|-----------|------------|
| Frontend | Next.js 14, Tailwind, shadcn/ui | Vercel |
| Gateway | Go (Gin) | Railway |
| RAG Service | FastAPI, e5-base, bge-reranker | Railway |
| Planner Service | FastAPI, OpenRouter | Railway |
| Quiz Service | FastAPI, OpenRouter | Railway |
| Vector DB | Qdrant | Qdrant Cloud |
| Relational DB | Postgres | Neon/Supabase |
| Auth | Supabase Auth | Supabase |
| Storage | Supabase Storage | Supabase |
| Observability | PostHog, Sentry | Cloud |

---

## Migration Path to AWS

When ready to migrate:
1. Replace Railway → ECS Fargate
2. Replace Neon → RDS Postgres
3. Replace Supabase Auth → Cognito
4. Replace Supabase Storage → S3
5. Add Terraform for IaC
6. Add CloudWatch + X-Ray

All API contracts remain unchanged.
