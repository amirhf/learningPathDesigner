Learning Path Designer — MVP (Lean Deploy Design)
1) Executive Summary
This revision prioritizes fastest time-to-demo with minimal infrastructure and zero Terraform. We replace bespoke
AWS setup with managed platforms and one-click deploys, while keeping the AWS target viable later. Goal: public
URL in hours, not days.

2) Principles
Prefer managed services with free tiers. • No Terraform in MVP; use platform dashboards and env vars. • Keep
APIs, data model, and prompts unchanged so migration to AWS/ECS later is trivial. • Provide Docker Compose for
local dev parity.
3) Lean Stack Choices
Layer Choice (MVP) Why / Migration path
Frontend Next.js on Vercel Instant HTTPS, previews; later → Amplify or S3+CloudFront
Gateway (Go) Railway (Docker) or Fly.io 1-click deploy; later → ECS/Lambda
RAG/Planner/Quiz (FastAPI)Railway (3 services) or Render Auto-build; later → ECS or EKS
Vector DB Qdrant Cloud (Free tier) No ops; later → self-host Qdrant on AWS
Relational DB Neon/Postgres or Supabase Serverless, branches; later → RDS
Auth Supabase Auth or Clerk Minutes to integrate; later → Cognito
Object Storage Supabase Storage (or S3) Simple SDK; later → S
Jobs/Cron Railway/Render cron + queues Good enough; later → SQS+Celery
Analytics PostHog + Sentry Quick product + error telemetry; later → CloudWatch/X-Ray
4) Architecture (Lean Variant)
Vercel (FE) → Gateway (Go on Railway) → FastAPI services (Railway) → Qdrant Cloud, Neon/Supabase. All
services use platform env vars; secrets stored in Vercel/Supabase/Railway dashboards. Logs via platform consoles;
PostHog events + Sentry errors.

5) Deployment in ~60–90 minutes
Create Qdrant Cloud project; get API key + URL.
Create Neon or Supabase Postgres; copy connection string.
Create Supabase project (if chosen) for Auth + Storage; get anon/public & service keys.
Fork repo. Connect Vercel to /frontend; set env vars; deploy.
Create three Railway services from repo subfolders: /gateway, /services/rag, /services/planner, /services/quiz
(three or merge planner+quiz). Set env vars; deploy.
Run ingestion job via Railway one-off or GitHub Action to seed 150–300 resources.
6) Environment Variables Matrix
Name Used by Example
Name Used by Example
DATABASE_URL Gateway/Services postgres://user:pass@host/db
QDRANT_URL rag-service https://xxxx.qdrant.tech
QDRANT_API_KEY rag-service qdrant_xxx
OPENROUTER_API_KEY planner/quiz sk-or-xxx
E5_MODEL_NAME rag-service intfloat/e5-base
RERANKER_MODEL_NAME rag-service BAAI/bge-reranker-base
AUTH_JWT_PUBLIC_KEY Gateway <pem or jwks url>
SUPABASE_URL Frontend https://xxxxx.supabase.co
SUPABASE_ANON_KEY Frontend eyJ...
STORAGE_BUCKET rag/quiz lpd-snippets
7) Minimal Changes from Previous Design
API contracts unchanged. • Data model unchanged. • Prompt schemas unchanged. • Swap Celery+SQS for
platform cron + simple in-service worker. • Replace Cognito with Supabase Auth (JWT verification in Go).
8) Local Dev with Docker Compose
services:
qdrant:
image: qdrant/qdrant:latest
ports: ["6333:6333"]
db:
image: postgres:
environment:
POSTGRES_PASSWORD: postgres
ports: ["5432:5432"]
rag:
build: ./services/rag
env_file: .env
planner:
build: ./services/planner
env_file: .env
quiz:
build: ./services/quiz
env_file: .env
gateway:
build: ./gateway
env_file: .env
ports: ["8080:8080"]

9) Ingestion Plan (No-ops Friendly)
Ship a CLI python -m ingestion.seed --limit 300 that reads the seed CSV/JSON, fetches metadata/snippets,
embeds via e5-base, and upserts into Qdrant + Postgres. Provide a GitHub Action workflow_dispatch to run it
remotely with repo secrets.

10) Monitoring & Alerts (No Terraform)
Vercel: deployment + request analytics. • Railway: service logs, metrics. • PostHog: product events. • Sentry (FE +
BE): error tracking. • UptimeRobot (free) for health checks.
11) Risks & Backout
Vendor limits (free tiers) → mitigate by lowering top-k and batching. If Railway limits hit, move one service to
Render/Fly. All stateful pieces (Qdrant, DB) are managed services so services can be redeployed statelessly.

12) API Contracts, Schemas, Prompts (Unchanged)
See the previous full design document; all interfaces remain stable. This lean deploy plan only changes where
services run and how secrets are provided.

13) Quick Demo Checklist
Create goal (4 weeks, 6h/w, Intermediate) → plan appears.
Open lesson → grounded summary with citations.
Take quiz (2–4 Q) → grading works.
Skip lesson → Replan swaps shorter resource → show diff.
Share public read-only link.