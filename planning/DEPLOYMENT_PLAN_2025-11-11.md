# Learning Path Designer - Public Deployment Plan
**Date:** 2025-11-11  
**Status:** Ready for Deployment  
**Estimated Time:** 4-6 hours  
**Monthly Cost:** $15-50 (free tiers + minimal paid)

---

## Executive Summary

Deploy the Learning Path Designer to production using managed services:
- **Frontend:** Vercel (Next.js)
- **Backend:** Railway (Go Gateway + 3 Python services)
- **Database:** Neon PostgreSQL
- **Vector DB:** Qdrant Cloud
- **Auth/Storage:** Supabase

**Current State:** 98% complete, all services tested locally, ready for production.

---

## Architecture

```
Vercel (Frontend) → Railway (Gateway) → Railway (RAG/Planner/Quiz)
                                         ↓
                                    Qdrant Cloud + Neon + Supabase
```

---

## Phase 1: Infrastructure Setup (60 min)

### 1.1 Qdrant Cloud (10 min)
1. Sign up at https://cloud.qdrant.io
2. Create cluster: `learnpath-prod` (Free tier: 1GB)
3. Save: `QDRANT_URL` and `QDRANT_API_KEY`

### 1.2 Neon PostgreSQL (10 min)
1. Sign up at https://neon.tech
2. Create project: `learnpath-prod`
3. Create database: `learnpath`
4. Save: `DATABASE_URL`

### 1.3 Supabase (15 min)
1. Sign up at https://supabase.com
2. Create project: `learnpath-prod`
3. Enable Email authentication
4. Create storage bucket: `learnpath-snippets` (private)
5. Save: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`

### 1.4 OpenRouter (5 min)
1. Sign up at https://openrouter.ai
2. Get API key
3. Save: `OPENROUTER_API_KEY`

### 1.5 Railway (20 min)
1. Sign up at https://railway.app with GitHub
2. Create project: `learnpath-prod`
3. Connect GitHub repository
4. Create 4 services:
   - `gateway` (from `/gateway`)
   - `rag-service` (from `/services/rag`)
   - `planner-service` (from `/services/planner`)
   - `quiz-service` (from `/services/quiz`)

---

## Phase 2: Environment Variables

Create `.env.production` with all required variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/learnpath?sslmode=require

# Qdrant
QDRANT_URL=https://xxxxx.qdrant.tech:6333
QDRANT_API_KEY=your_key
QDRANT_COLLECTION=resources

# AI Models
OPENROUTER_API_KEY=sk-or-xxxxx
E5_MODEL_NAME=intfloat/e5-base-v2
RERANKER_MODEL_NAME=BAAI/bge-reranker-base
LLM_MODEL=anthropic/claude-3.5-sonnet

# Optimization
USE_QUANTIZATION=true
QUANTIZATION_CONFIG=int8

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGc...
SUPABASE_SERVICE_KEY=eyJhbGc...
JWT_PUBLIC_KEY_URL=https://xxxxx.supabase.co/auth/v1/jwks
STORAGE_BUCKET=learnpath-snippets

# Service URLs (Railway internal)
RAG_SERVICE_URL=https://rag-service.railway.app
PLANNER_SERVICE_URL=https://planner-service.railway.app
QUIZ_SERVICE_URL=https://quiz-service.railway.app

# Gateway
GATEWAY_PORT=8080
ALLOWED_ORIGINS=https://your-app.vercel.app
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Frontend (Vercel)
NEXT_PUBLIC_API_URL=https://gateway.railway.app
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Observability
LOG_LEVEL=info
DEBUG=false
```

**Set in Railway:**
- Go to each service → Variables → Add all relevant variables

**Set in Vercel:**
- Project Settings → Environment Variables → Add frontend variables

---

## Phase 3: Backend Deployment (90 min)

### Deploy Order (Important!)

#### 3.1 RAG Service
```bash
# Railway will auto-deploy from GitHub
# Or manually: railway up --service rag-service
```
**Verify:** `curl https://rag-service.railway.app/health`

**Note:** First build takes 5-10 min (downloads ML models)

#### 3.2 Planner Service
```bash
railway up --service planner-service
```
**Verify:** `curl https://planner-service.railway.app/health`

#### 3.3 Quiz Service
```bash
railway up --service quiz-service
```
**Verify:** `curl https://quiz-service.railway.app/health`

#### 3.4 Gateway
Update service URLs in Railway variables, then deploy:
```bash
railway up --service gateway
```
**Verify:** `curl https://gateway.railway.app/health`

---

## Phase 4: Frontend Deployment (30 min)

### 4.1 Vercel Setup
1. Go to https://vercel.com
2. Import GitHub repository
3. Configure:
   - **Framework:** Next.js
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
4. Add environment variables (see Phase 2)
5. Deploy

### 4.2 Verify
- Visit `https://your-app.vercel.app`
- Check browser console for errors
- Test basic navigation

---

## Phase 5: Database & Data (60 min)

### 5.1 Run Migrations
```bash
# Option A: Via Railway CLI
railway run psql $DATABASE_URL < shared/migrations/001_initial_schema.sql
railway run psql $DATABASE_URL < shared/migrations/002_service_tables.sql

# Option B: Direct psql
psql "$DATABASE_URL" -f shared/migrations/001_initial_schema.sql
psql "$DATABASE_URL" -f shared/migrations/002_service_tables.sql
```

### 5.2 Seed Data

**Create GitHub Action** (`.github/workflows/seed-data.yml`):
```yaml
name: Seed Production Data
on:
  workflow_dispatch:

jobs:
  seed:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r ingestion/requirements.txt
      - name: Seed skills
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python -m ingestion.seed_skills
      - name: Setup Qdrant
        env:
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
        run: python -m ingestion.setup_qdrant
      - name: Ingest resources
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          QDRANT_URL: ${{ secrets.QDRANT_URL }}
          QDRANT_API_KEY: ${{ secrets.QDRANT_API_KEY }}
        run: python -m ingestion.ingest --seed ingestion/seed_resources.json --limit 500
```

**Run manually:**
```bash
export DATABASE_URL="..."
export QDRANT_URL="..."
export QDRANT_API_KEY="..."

python -m ingestion.seed_skills
python -m ingestion.setup_qdrant
python -m ingestion.ingest --seed ingestion/seed_resources.json --limit 500
```

### 5.3 Verify Data
```sql
SELECT COUNT(*) FROM resources;  -- Should have ~500
SELECT COUNT(*) FROM skills;     -- Should have ~50+
```

---

## Phase 6: Security Configuration

### 6.1 Enable Authentication
- JWT validation already in gateway code
- Ensure `JWT_PUBLIC_KEY_URL` is set correctly
- Test with Supabase auth tokens

### 6.2 Configure CORS
Update gateway environment:
```bash
ALLOWED_ORIGINS=https://your-app.vercel.app,https://*.vercel.app
```

### 6.3 Rate Limiting
Already configured in gateway. Adjust if needed:
```bash
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

---

## Phase 7: Testing & Go-Live (30 min)

### 7.1 Smoke Tests
```bash
# Health checks
curl https://gateway.railway.app/health
curl https://rag-service.railway.app/health
curl https://planner-service.railway.app/health
curl https://quiz-service.railway.app/health

# Search test
curl -X POST https://gateway.railway.app/api/search \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query": "learn python", "top_k": 5}'
```

### 7.2 End-to-End Test
1. Visit frontend
2. Sign up / Sign in
3. Search for resources
4. Create learning plan
5. Generate quiz
6. Submit answers
7. Check dashboard

### 7.3 Monitor
- Check Railway metrics (CPU, memory)
- Check Sentry for errors (if configured)
- Monitor response times

---

## Monitoring Setup

### Essential Monitoring

**Railway Built-in:**
- CPU/Memory usage per service
- Request counts
- Response times
- Access: Railway Dashboard → Service → Metrics

**Uptime Monitoring (Free):**
1. Sign up at https://uptimerobot.com
2. Add monitors:
   - `https://your-app.vercel.app`
   - `https://gateway.railway.app/health`
3. Set up email alerts

### Optional: Advanced Monitoring

**Sentry (Error Tracking):**
```bash
# Add to environment
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
```

**PostHog (Analytics):**
```bash
# Add to frontend
NEXT_PUBLIC_POSTHOG_KEY=phc_xxxxx
```

---

## Rollback Plan

### Quick Rollback

**Railway:**
1. Dashboard → Service → Deployments
2. Select previous working deployment
3. Click "Redeploy"

**Vercel:**
1. Dashboard → Deployments
2. Select previous deployment
3. Click "Promote to Production"

### Database Backup
```bash
# Before schema changes
pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql

# Restore if needed
psql "$DATABASE_URL" < backup_20251111.sql
```

---

## Cost Breakdown

### Free Tier (0-100 users)
- Vercel: $0
- Railway: $5 credit/month
- Qdrant: $0 (1GB free)
- Neon: $0 (0.5GB free)
- Supabase: $0 (500MB free)
- OpenRouter: ~$10-20/month
**Total: $15-30/month**

### Growth (100-1000 users)
- Vercel: $20/month
- Railway: $50-100/month
- Qdrant: $25/month
- Neon: $19/month
- Supabase: $25/month
- OpenRouter: $50-100/month
**Total: $189-289/month**

---

## Post-Deployment Checklist

### Day 1
- [ ] All health checks green
- [ ] Test critical user flows
- [ ] Monitor error rates
- [ ] Check resource usage
- [ ] Set up uptime alerts

### Week 1
- [ ] Monitor LLM API costs
- [ ] Analyze user behavior
- [ ] Optimize slow queries
- [ ] Collect user feedback
- [ ] Fix critical bugs

### Month 1
- [ ] Set up automated backups
- [ ] Create staging environment
- [ ] Add comprehensive tests
- [ ] Optimize database indexes
- [ ] Implement caching

---

## Troubleshooting

### Service Won't Start
- Check environment variables
- Verify database connection
- Check Railway logs: `railway logs --service SERVICE_NAME`
- Ensure health check endpoint works

### High Latency
- Check service resource usage
- Verify database connection pooling
- Enable caching
- Scale horizontally

### Authentication Failures
- Verify JWT public key URL
- Check Supabase settings
- Ensure CORS configured
- Verify token expiration

### Database Connection Errors
- Check connection string format
- Verify SSL mode
- Check Neon project active
- Verify IP allowlist

---

## Next Steps After Deployment

1. **Gather User Feedback** - Share with beta users
2. **Monitor Performance** - Track response times and errors
3. **Optimize Costs** - Review LLM usage, implement caching
4. **Add Features** - Based on user feedback
5. **Scale Infrastructure** - As user base grows

---

## Support & Resources

- **Railway Docs:** https://docs.railway.app
- **Vercel Docs:** https://vercel.com/docs
- **Qdrant Docs:** https://qdrant.tech/documentation
- **Neon Docs:** https://neon.tech/docs
- **Supabase Docs:** https://supabase.com/docs

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-11  
**Next Review:** After first production deployment
