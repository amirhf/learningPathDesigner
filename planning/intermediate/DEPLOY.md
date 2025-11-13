# Quick Deployment Guide

**Time Required:** 4-6 hours  
**Cost:** $15-50/month (starting with free tiers)

---

## Overview

This guide walks you through deploying the Learning Path Designer to production using managed services.

**Stack:**
- **Frontend:** Vercel (Next.js)
- **Backend:** Railway (Go + Python services)
- **Database:** Neon PostgreSQL
- **Vector DB:** Qdrant Cloud
- **Auth/Storage:** Supabase

---

## Prerequisites

✅ GitHub account  
✅ Credit card (for free trial signups)  
✅ OpenRouter API key ([get one here](https://openrouter.ai))  
✅ 4-6 hours of time

---

## Step-by-Step Deployment

### Step 1: Create Accounts (20 minutes)

Sign up for these services (all have free tiers):

1. **Qdrant Cloud** → https://cloud.qdrant.io
2. **Neon** → https://neon.tech
3. **Supabase** → https://supabase.com
4. **Railway** → https://railway.app (sign in with GitHub)
5. **Vercel** → https://vercel.com (sign in with GitHub)

---

### Step 2: Set Up Qdrant (10 minutes)

1. Create cluster: `learnpath-prod`
2. Choose region closest to your users
3. Select **Free tier** (1GB)
4. Save these values:
   ```
   QDRANT_URL=https://xxxxx.qdrant.tech:6333
   QDRANT_API_KEY=your_api_key
   ```

---

### Step 3: Set Up Neon PostgreSQL (10 minutes)

1. Create project: `learnpath-prod`
2. Create database: `learnpath`
3. Copy connection string from dashboard
4. Save:
   ```
   DATABASE_URL=postgresql://user:pass@host/learnpath?sslmode=require
   ```

---

### Step 4: Set Up Supabase (15 minutes)

1. Create project: `learnpath-prod`
2. Go to **Authentication** → Enable Email provider
3. Set Site URL to your future Vercel URL (can update later)
4. Go to **Storage** → Create bucket: `learnpath-snippets` (private)
5. Save these values:
   ```
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=eyJhbGc...
   SUPABASE_SERVICE_KEY=eyJhbGc...
   ```

---

### Step 5: Deploy Backend to Railway (60 minutes)

1. **Create Railway Project**
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Connect your repository

2. **Create 4 Services**
   
   For each service, click "New Service" → "GitHub Repo":
   
   **Service 1: RAG Service**
   - Name: `rag-service`
   - Root directory: `/services/rag`
   - Add environment variables (see below)
   
   **Service 2: Planner Service**
   - Name: `planner-service`
   - Root directory: `/services/planner`
   - Add environment variables (see below)
   
   **Service 3: Quiz Service**
   - Name: `quiz-service`
   - Root directory: `/services/quiz`
   - Add environment variables (see below)
   
   **Service 4: Gateway**
   - Name: `gateway`
   - Root directory: `/gateway`
   - Add environment variables (see below)

3. **Add Environment Variables**

   For **RAG Service**:
   ```bash
   DATABASE_URL=<from Neon>
   QDRANT_URL=<from Qdrant>
   QDRANT_API_KEY=<from Qdrant>
   QDRANT_COLLECTION=resources
   E5_MODEL_NAME=intfloat/e5-base-v2
   RERANKER_MODEL_NAME=BAAI/bge-reranker-base
   USE_QUANTIZATION=true
   QUANTIZATION_CONFIG=int8
   ```

   For **Planner Service**:
   ```bash
   DATABASE_URL=<from Neon>
   RAG_SERVICE_URL=https://rag-service.railway.app
   OPENROUTER_API_KEY=<your OpenRouter key>
   LLM_MODEL=anthropic/claude-3.5-sonnet
   ```

   For **Quiz Service**:
   ```bash
   DATABASE_URL=<from Neon>
   SUPABASE_URL=<from Supabase>
   SUPABASE_SERVICE_KEY=<from Supabase>
   STORAGE_BUCKET=learnpath-snippets
   OPENROUTER_API_KEY=<your OpenRouter key>
   LLM_MODEL=anthropic/claude-3.5-sonnet
   ```

   For **Gateway**:
   ```bash
   RAG_SERVICE_URL=https://rag-service.railway.app
   PLANNER_SERVICE_URL=https://planner-service.railway.app
   QUIZ_SERVICE_URL=https://quiz-service.railway.app
   JWT_PUBLIC_KEY_URL=https://xxxxx.supabase.co/auth/v1/jwks
   ALLOWED_ORIGINS=https://your-app.vercel.app
   RATE_LIMIT_REQUESTS=100
   RATE_LIMIT_WINDOW=60
   ```

4. **Deploy Services**
   - Railway will auto-deploy when you add the services
   - Wait for all builds to complete (~10 minutes)
   - Check that all services show "Active" status

5. **Verify Deployments**
   ```bash
   curl https://rag-service.railway.app/health
   curl https://planner-service.railway.app/health
   curl https://quiz-service.railway.app/health
   curl https://gateway.railway.app/health
   ```
   All should return `200 OK`

---

### Step 6: Deploy Frontend to Vercel (20 minutes)

1. **Import Project**
   - Go to https://vercel.com
   - Click "Add New" → "Project"
   - Import your GitHub repository

2. **Configure Build Settings**
   - Framework Preset: **Next.js**
   - Root Directory: **frontend**
   - Build Command: `npm run build`
   - Output Directory: `.next`

3. **Add Environment Variables**
   ```bash
   NEXT_PUBLIC_API_URL=https://gateway.railway.app
   NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=<from Supabase>
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (~5 minutes)
   - Visit your site at `https://your-app.vercel.app`

5. **Update CORS**
   - Go back to Railway → Gateway service
   - Update `ALLOWED_ORIGINS` with your actual Vercel URL
   - Redeploy gateway

---

### Step 7: Set Up Database (30 minutes)

1. **Run Migrations**
   
   Option A - Using Railway CLI:
   ```bash
   railway link
   railway run psql $DATABASE_URL < shared/migrations/001_initial_schema.sql
   railway run psql $DATABASE_URL < shared/migrations/002_service_tables.sql
   ```
   
   Option B - Using local psql:
   ```bash
   psql "postgresql://user:pass@host/learnpath?sslmode=require" \
     -f shared/migrations/001_initial_schema.sql
   psql "postgresql://user:pass@host/learnpath?sslmode=require" \
     -f shared/migrations/002_service_tables.sql
   ```

2. **Seed Data via GitHub Actions**
   
   - Go to your GitHub repository
   - Click "Actions" tab
   - Select "Seed Production Data" workflow
   - Click "Run workflow"
   - Enter resource limit (e.g., 500)
   - Click "Run workflow"
   - Wait for completion (~10-15 minutes)

3. **Verify Data**
   ```bash
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM resources;"
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM skills;"
   ```

---

### Step 8: Test Everything (20 minutes)

1. **Run Health Checks**
   ```bash
   # PowerShell
   .\ops\deploy-check.ps1 `
     -GatewayUrl "https://gateway.railway.app" `
     -FrontendUrl "https://your-app.vercel.app"
   
   # Bash
   ./ops/deploy-check.sh
   ```

2. **Test End-to-End Flow**
   - Visit your Vercel URL
   - Sign up for an account
   - Search for resources
   - Create a learning plan
   - Generate a quiz
   - Submit quiz answers
   - Check dashboard

3. **Verify Everything Works**
   - ✅ Pages load without errors
   - ✅ Search returns results
   - ✅ Plan generation succeeds
   - ✅ Quiz generation succeeds
   - ✅ Data persists correctly

---

## Step 9: Set Up Monitoring (15 minutes)

1. **UptimeRobot (Free)**
   - Sign up at https://uptimerobot.com
   - Add monitors:
     - `https://your-app.vercel.app`
     - `https://gateway.railway.app/health`
   - Set up email alerts

2. **Railway Metrics**
   - Check CPU/Memory usage for each service
   - Set up alerts if usage is high

---

## You're Done! 🎉

Your Learning Path Designer is now live at:
- **Frontend:** https://your-app.vercel.app
- **API:** https://gateway.railway.app

---

## Next Steps

### Immediate
- [ ] Share URL with beta users
- [ ] Monitor logs for errors
- [ ] Check resource usage

### Week 1
- [ ] Monitor LLM API costs
- [ ] Collect user feedback
- [ ] Fix any bugs

### Month 1
- [ ] Set up automated backups
- [ ] Add more resources to database
- [ ] Optimize performance

---

## Troubleshooting

### Service Won't Start
- Check environment variables are set correctly
- View logs in Railway dashboard
- Verify database connection string

### Frontend Can't Connect to Backend
- Check `NEXT_PUBLIC_API_URL` is correct
- Verify CORS settings in gateway
- Check browser console for errors

### Database Connection Failed
- Verify `DATABASE_URL` format
- Check Neon project is active
- Ensure SSL mode is enabled

### Need Help?
- Check full deployment plan: `planning/DEPLOYMENT_PLAN_2025-11-11.md`
- Check deployment checklist: `DEPLOYMENT_CHECKLIST.md`
- Review Railway logs: `railway logs --service SERVICE_NAME`

---

## Cost Monitoring

Keep an eye on these costs:
- **OpenRouter:** Check usage at https://openrouter.ai/activity
- **Railway:** Check usage in Railway dashboard
- **Vercel:** Check bandwidth in Vercel dashboard

**Expected costs:** $15-30/month for MVP (0-100 users)

---

## Rollback

If something goes wrong:

**Railway:**
1. Go to service → Deployments
2. Find previous working deployment
3. Click "Redeploy"

**Vercel:**
1. Go to project → Deployments
2. Find previous deployment
3. Click "Promote to Production"

---

**Need the detailed plan?** See `planning/DEPLOYMENT_PLAN_2025-11-11.md`

**Need the checklist?** See `DEPLOYMENT_CHECKLIST.md`
