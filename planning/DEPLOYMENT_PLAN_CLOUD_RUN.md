# Learning Path Designer - Google Cloud Run Deployment Plan
**Date:** 2025-11-11  
**Status:** Ready for Deployment  
**Estimated Time:** 4-6 hours  
**Monthly Cost:** $20-60 (with Cloud Run free tier)

---

## Executive Summary

Deploy the Learning Path Designer to production using Google Cloud Run for backend services:
- **Frontend:** Vercel (Next.js)
- **Backend:** Google Cloud Run (Go Gateway + 3 Python services)
- **Database:** Neon PostgreSQL
- **Vector DB:** Qdrant Cloud
- **Auth/Storage:** Supabase

**Advantages of Cloud Run:**
- Pay only for actual usage (billed per 100ms)
- Automatic scaling (0 to N instances)
- Built-in load balancing
- Native Docker support
- Free tier: 2 million requests/month
- Better pricing for sporadic traffic

---

## Architecture

```
Vercel (Frontend) → Cloud Run (Gateway) → Cloud Run (RAG/Planner/Quiz)
                                           ↓
                                      Qdrant Cloud + Neon + Supabase
```

---

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed
- Docker installed locally
- All other accounts (Vercel, Qdrant, Neon, Supabase)

---

## Phase 1: Google Cloud Setup (30 minutes)

### 1.1 Install Google Cloud CLI

**Windows (PowerShell):**
```powershell
# Download and install from:
# https://cloud.google.com/sdk/docs/install

# Or via Chocolatey:
choco install gcloudsdk
```

**Linux/Mac:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

### 1.2 Initialize gcloud

```bash
# Login to Google Cloud
gcloud auth login

# Create new project
gcloud projects create learnpath-prod --name="Learning Path Designer"

# Set as default project
gcloud config set project learnpath-prod

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Set default region (choose closest to your users)
gcloud config set run/region europe-west1
```

### 1.3 Enable Billing

1. Go to https://console.cloud.google.com/billing
2. Link billing account to `learnpath-prod` project
3. Verify billing is enabled

---

## Phase 2: Set Up Secrets (20 minutes)

Google Cloud Secret Manager provides secure storage for sensitive data.

### 2.1 Create Secrets

```bash
# Database URL
echo -n "postgresql://neondb_owner:npg_ngvLs9Uy5hIj@ep-old-hat-agayfjks-pooler.c-2.eu-central-1.aws.neon.tech/learnpath?sslmode=require" | \
Write-Output -NoNewline "postgresql://neondb_owner:npg_ngvLs9Uy5hIj@ep-old-hat-agayfjks-pooler.c-2.eu-central-1.aws.neon.tech/learnpath?sslmode=require" | gcloud secrets create database-url --data-file=-  

# Qdrant credentials
echo -n "https://e9564da9-e5d0-4c8e-a06d-0200efcaed0c.europe-west3-0.gcp.cloud.qdrant.io:6333" | \
Write-Output -NoNewline "https://e9564da9-e5d0-4c8e-a06d-0200efcaed0c.europe-west3-0.gcp.cloud.qdrant.io:6333" |  gcloud secrets create qdrant-url --data-file=-

echo -n "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.FaX9XN1yo76G4DkLia3WnjjuaQusOHfPbCd8jjB4xMc" | \
Write-Output -NoNewline "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.FaX9XN1yo76G4DkLia3WnjjuaQusOHfPbCd8jjB4xMc" | gcloud secrets create qdrant-api-key --data-file=-

# OpenRouter API key
echo -n "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" | \
Write-Output -NoNewline "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" | gcloud secrets create openrouter-api-key --data-file=-

# Supabase credentials
echo -n "https://hywmzhvyhiynewfsmqln.supabase.co" | \
Write-Output -NoNewline "https://hywmzhvyhiynewfsmqln.supabase.co" | gcloud secrets create supabase-url --data-file=-

echo -n "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5d216aHZ5aGl5bmV3ZnNtcWxuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NjM5NjcsImV4cCI6MjA3ODQzOTk2N30.NNZ_3lWeO6i5xN0DmPZeVaS7Zyn4JgFzqkr3n-7Vdcc" | \
Write-Output -NoNewlin "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5d216aHZ5aGl5bmV3ZnNtcWxuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NjM5NjcsImV4cCI6MjA3ODQzOTk2N30.NNZ_3lWeO6i5xN0DmPZeVaS7Zyn4JgFzqkr3n-7Vdcc" |  gcloud secrets create supabase-anon-key --data-file=-

echo -n "YOUR_SERVICE_KEY_HERE" | \
  gcloud secrets create supabase-service-key --data-file=-

# List all secrets
gcloud secrets list
```

### 2.2 Grant Access to Cloud Run

```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe learnpath-prod --format="value(projectNumber)")

# Grant Secret Manager access to Cloud Run service account
gcloud projects add-iam-policy-binding learnpath-prod `
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

---

## Phase 3: Build and Push Docker Images (10 minutes)

**⚡ Recommended: Use Cloud Build (builds in the cloud, much faster!)**

Cloud Build builds your Docker images in Google's infrastructure, which is much faster than building locally and uploading with slow internet.

### Option A: Cloud Build (Recommended) ⭐

**Build only (no deployment):**
```powershell
# PowerShell
.\ops\cloud-build-deploy.ps1 -BuildOnly

# Bash
BUILD_ONLY=true ./ops/cloud-build-deploy.sh
```

**Build AND deploy (all in one):**
```powershell
# PowerShell
.\ops\cloud-build-deploy.ps1 -ProjectId "learnpath-prod" -Region "europe-west1"

# Bash
./ops/cloud-build-deploy.sh
```

**Or manually submit:**
```bash
# Build images only
gcloud builds submit --config cloudbuild.yaml .

# Build and deploy
gcloud builds submit --config cloudbuild-deploy.yaml \
  --substitutions="_REGION=europe-west1,_ALLOWED_ORIGINS=https://your-app.vercel.app" .
```

**Advantages:**
- ✅ Builds in Google's cloud (fast network)
- ✅ No need to upload large images
- ✅ Parallel builds (faster)
- ✅ Automatic retry on failure
- ✅ Build logs in Cloud Console

**Time:** ~10 minutes (vs 40+ minutes locally with slow internet)

**Cost:** Free tier includes 120 build-minutes/day

---

### Option B: Local Build (If you prefer)

Only use this if you have fast internet or want to build locally.

**Configure Docker:**
```bash
gcloud auth configure-docker
```

**Build and push all services:**
```bash
# RAG Service
cd services/rag
docker build -t gcr.io/learnpath-prod/rag-service:latest .
docker push gcr.io/learnpath-prod/rag-service:latest

# Planner Service
cd ../planner
docker build -t gcr.io/learnpath-prod/planner-service:latest .
docker push gcr.io/learnpath-prod/planner-service:latest

# Quiz Service
cd ../quiz
docker build -t gcr.io/learnpath-prod/quiz-service:latest .
docker push gcr.io/learnpath-prod/quiz-service:latest

# Gateway
cd ../../gateway
docker build -t gcr.io/learnpath-prod/gateway:latest .
docker push gcr.io/learnpath-prod/gateway:latest
```

**Note:** RAG service image is ~2-3GB due to ML models. With slow internet, this can take 30+ minutes to upload.

---

## Phase 4: Deploy Services to Cloud Run (60 minutes)

### 4.1 Deploy RAG Service

```bash
gcloud run deploy rag-service \
  --image gcr.io/learnpath-prod/rag-service:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 10 \
  --set-secrets="DATABASE_URL=database-url:latest,QDRANT_URL=qdrant-url:latest,QDRANT_API_KEY=qdrant-api-key:latest" \
  --set-env-vars="QDRANT_COLLECTION=resources,E5_MODEL_NAME=intfloat/e5-base-v2,RERANKER_MODEL_NAME=BAAI/bge-reranker-base,USE_QUANTIZATION=true,QUANTIZATION_CONFIG=int8,LOG_LEVEL=info"
```

**Get the service URL:**
```bash
RAG_URL=$(gcloud run services describe rag-service --region europe-west1 --format="value(status.url)")
echo "RAG Service URL: $RAG_URL"
```

**Verify:**
```bash
curl $RAG_URL/health
```

### 4.2 Deploy Planner Service

```bash
gcloud run deploy planner-service \
  --image gcr.io/learnpath-prod/planner-service:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 20 \
  --min-instances 0 \
  --max-instances 10 \
  --set-secrets="DATABASE_URL=database-url:latest,OPENROUTER_API_KEY=openrouter-api-key:latest" \
  --set-env-vars="RAG_SERVICE_URL=$RAG_URL,LLM_MODEL=anthropic/claude-3.5-sonnet,LOG_LEVEL=info"
```

**Get the service URL:**
```bash
PLANNER_URL=$(gcloud run services describe planner-service --region europe-west1 --format="value(status.url)")
echo "Planner Service URL: $PLANNER_URL"
```

**Verify:**
```bash
curl $PLANNER_URL/health
```

### 4.3 Deploy Quiz Service

```bash
gcloud run deploy quiz-service \
  --image gcr.io/learnpath-prod/quiz-service:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 20 \
  --min-instances 0 \
  --max-instances 10 \
  --set-secrets="DATABASE_URL=database-url:latest,OPENROUTER_API_KEY=openrouter-api-key:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_SERVICE_KEY=supabase-service-key:latest" \
  --set-env-vars="STORAGE_BUCKET=learnpath-snippets,LLM_MODEL=anthropic/claude-3.5-sonnet,LOG_LEVEL=info"
```

**Get the service URL:**
```bash
QUIZ_URL=$(gcloud run services describe quiz-service --region europe-west1 --format="value(status.url)")
echo "Quiz Service URL: $QUIZ_URL"
```

**Verify:**
```bash
curl $QUIZ_URL/health
```

### 4.4 Deploy Gateway

```bash
gcloud run deploy gateway \
  --image gcr.io/learnpath-prod/gateway:latest \
  --platform managed \
  --region europe-west1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 20 \
  --set-secrets="SUPABASE_URL=supabase-url:latest" \
  --set-env-vars="RAG_SERVICE_URL=$RAG_URL,PLANNER_SERVICE_URL=$PLANNER_URL,QUIZ_SERVICE_URL=$QUIZ_URL,JWT_PUBLIC_KEY_URL=https://hywmzhvyhiynewfsmqln.supabase.co/auth/v1/jwks,ALLOWED_ORIGINS=https://your-app.vercel.app,RATE_LIMIT_REQUESTS=100,RATE_LIMIT_WINDOW=60,LOG_LEVEL=info"
```

**Get the service URL:**
```bash
GATEWAY_URL=$(gcloud run services describe gateway --region europe-west1 --format="value(status.url)")
echo "Gateway URL: $GATEWAY_URL"
```

**Verify:**
```bash
curl $GATEWAY_URL/health
```

---

## Phase 5: Deploy Frontend to Vercel (20 minutes)

### 5.1 Update Environment Variables

In Vercel project settings, set:

```bash
NEXT_PUBLIC_API_URL=<GATEWAY_URL from above>
NEXT_PUBLIC_SUPABASE_URL=https://hywmzhvyhiynewfsmqln.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh5d216aHZ5aGl5bmV3ZnNtcWxuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI4NjM5NjcsImV4cCI6MjA3ODQzOTk2N30.NNZ_3lWeO6i5xN0DmPZeVaS7Zyn4JgFzqkr3n-7Vdcc
```

### 5.2 Deploy

```bash
cd frontend
vercel --prod
```

Or deploy via Vercel dashboard.

### 5.3 Update Gateway CORS

After getting your Vercel URL, update the gateway:

```bash
VERCEL_URL="https://your-app.vercel.app"

gcloud run services update gateway \
  --region europe-west1 \
  --update-env-vars="ALLOWED_ORIGINS=$VERCEL_URL"
```

---

## Phase 6: Database Setup (30 minutes)

### 6.1 Run Migrations

```bash
# Using your Neon connection string
psql "postgresql://neondb_owner:npg_ngvLs9Uy5hIj@ep-old-hat-agayfjks-pooler.c-2.eu-central-1.aws.neon.tech/learnpath?sslmode=require" \
  -f shared/migrations/001_initial_schema.sql

psql "postgresql://neondb_owner:npg_ngvLs9Uy5hIj@ep-old-hat-agayfjks-pooler.c-2.eu-central-1.aws.neon.tech/learnpath?sslmode=require" \
  -f shared/migrations/002_service_tables.sql
```

### 6.2 Seed Data

Use the GitHub Actions workflow or run locally:

```bash
export DATABASE_URL="postgresql://neondb_owner:npg_ngvLs9Uy5hIj@ep-old-hat-agayfjks-pooler.c-2.eu-central-1.aws.neon.tech/learnpath?sslmode=require"
export QDRANT_URL="https://e9564da9-e5d0-4c8e-a06d-0200efcaed0c.europe-west3-0.gcp.cloud.qdrant.io:6333"
export QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.FaX9XN1yo76G4DkLia3WnjjuaQusOHfPbCd8jjB4xMc"

python -m ingestion.seed_skills
python -m ingestion.setup_qdrant
python -m ingestion.ingest --seed ingestion/seed_resources.json --limit 500
```

---

## Phase 7: Testing (20 minutes)

### 7.1 Health Checks

```bash
# Get all service URLs
RAG_URL=$(gcloud run services describe rag-service --region europe-west1 --format="value(status.url)")
PLANNER_URL=$(gcloud run services describe planner-service --region europe-west1 --format="value(status.url)")
QUIZ_URL=$(gcloud run services describe quiz-service --region europe-west1 --format="value(status.url)")
GATEWAY_URL=$(gcloud run services describe gateway --region europe-west1 --format="value(status.url)")

# Test all services
curl $RAG_URL/health
curl $PLANNER_URL/health
curl $QUIZ_URL/health
curl $GATEWAY_URL/health
```

### 7.2 End-to-End Test

1. Visit your Vercel URL
2. Sign up / Sign in
3. Search for resources
4. Create a learning plan
5. Generate a quiz
6. Submit answers

---

## Cloud Run Configuration Details

### Resource Allocation

| Service | Memory | CPU | Concurrency | Min Instances | Max Instances |
|---------|--------|-----|-------------|---------------|---------------|
| RAG | 2Gi | 2 | 10 | 0 | 10 |
| Planner | 1Gi | 1 | 20 | 0 | 10 |
| Quiz | 1Gi | 1 | 20 | 0 | 10 |
| Gateway | 512Mi | 1 | 80 | 0 | 20 |

### Scaling Strategy

- **Min Instances: 0** - Scale to zero when idle (saves cost)
- **Max Instances:** Set based on expected load
- **Concurrency:** Number of requests per instance
- **Timeout:** 300s for AI services, 60s for gateway

### Cold Start Mitigation

For RAG service (has ML models):
```bash
# Keep 1 instance warm during business hours
gcloud run services update rag-service \
  --region europe-west1 \
  --min-instances 1
```

**Note:** This increases cost but eliminates cold starts.

---

## Cost Estimation

### Cloud Run Pricing (europe-west1)

**Free Tier (per month):**
- 2 million requests
- 360,000 GB-seconds memory
- 180,000 vCPU-seconds

**Paid Tier:**
- Requests: $0.40 per million
- Memory: $0.0000025 per GB-second
- CPU: $0.00001 per vCPU-second

### Estimated Monthly Costs

**Scenario 1: MVP (0-100 users, ~10K requests/month)**
- Cloud Run: $0-5 (within free tier)
- Qdrant Cloud: $0 (free tier)
- Neon: $0 (free tier)
- Supabase: $0 (free tier)
- Vercel: $0 (free tier)
- OpenRouter: $10-20
**Total: $10-25/month**

**Scenario 2: Growth (100-1000 users, ~100K requests/month)**
- Cloud Run: $20-40
- Qdrant Cloud: $25
- Neon: $19
- Supabase: $25
- Vercel: $20
- OpenRouter: $50-100
**Total: $159-229/month**

**Scenario 3: Scale (1000+ users, ~1M requests/month)**
- Cloud Run: $100-200
- Qdrant Cloud: $50
- Neon: $50
- Supabase: $50
- Vercel: $50
- OpenRouter: $200-500
**Total: $500-900/month**

---

## Monitoring & Observability

### Cloud Run Built-in Metrics

Access via Cloud Console:
- Request count
- Request latency
- Container CPU/Memory utilization
- Instance count
- Error rate

**View metrics:**
```bash
# Open Cloud Console
gcloud run services describe gateway --region europe-west1

# View logs
gcloud run logs read gateway --region europe-west1 --limit 50
```

### Set Up Alerts

```bash
# Create alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s
```

### External Monitoring

Use the same tools as Railway plan:
- **UptimeRobot** - Uptime monitoring
- **Sentry** - Error tracking
- **PostHog** - Analytics

---

## Deployment Automation

### Create Deployment Script

Create `ops/deploy-cloud-run.sh`:

```bash
#!/bin/bash
set -e

PROJECT_ID="learnpath-prod"
REGION="europe-west1"

echo "Building and deploying to Cloud Run..."

# Build and push images
services=("rag-service" "planner-service" "quiz-service" "gateway")

for service in "${services[@]}"; do
  echo "Building $service..."
  
  if [ "$service" = "gateway" ]; then
    cd gateway
  else
    cd services/${service%-service}
  fi
  
  docker build -t gcr.io/$PROJECT_ID/$service:latest .
  docker push gcr.io/$PROJECT_ID/$service:latest
  
  echo "Deploying $service..."
  gcloud run deploy $service \
    --image gcr.io/$PROJECT_ID/$service:latest \
    --region $REGION \
    --quiet
  
  cd -
done

echo "Deployment complete!"
```

### CI/CD with Cloud Build

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build RAG Service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/rag-service', './services/rag']
  
  # Build Planner Service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/planner-service', './services/planner']
  
  # Build Quiz Service
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/quiz-service', './services/quiz']
  
  # Build Gateway
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/gateway', './gateway']
  
  # Deploy RAG Service
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - 'gcloud'
      - 'run'
      - 'deploy'
      - 'rag-service'
      - '--image=gcr.io/$PROJECT_ID/rag-service'
      - '--region=europe-west1'
      - '--platform=managed'
  
  # Deploy other services...

images:
  - 'gcr.io/$PROJECT_ID/rag-service'
  - 'gcr.io/$PROJECT_ID/planner-service'
  - 'gcr.io/$PROJECT_ID/quiz-service'
  - 'gcr.io/$PROJECT_ID/gateway'
```

---

## Security Best Practices

### 1. Service-to-Service Authentication

Enable IAM authentication between services:

```bash
# Remove public access
gcloud run services remove-iam-policy-binding rag-service \
  --region europe-west1 \
  --member="allUsers" \
  --role="roles/run.invoker"

# Grant gateway access to RAG service
gcloud run services add-iam-policy-binding rag-service \
  --region europe-west1 \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 2. VPC Connector (Optional)

For private networking:

```bash
# Create VPC connector
gcloud compute networks vpc-access connectors create learnpath-connector \
  --region europe-west1 \
  --range 10.8.0.0/28

# Use in Cloud Run
gcloud run services update gateway \
  --region europe-west1 \
  --vpc-connector learnpath-connector
```

### 3. Secret Rotation

```bash
# Update a secret
echo -n "new-value" | gcloud secrets versions add database-url --data-file=-

# Cloud Run will automatically use the latest version
```

---

## Rollback Procedures

### Rollback to Previous Revision

```bash
# List revisions
gcloud run revisions list --service gateway --region europe-west1

# Rollback to specific revision
gcloud run services update-traffic gateway \
  --region europe-west1 \
  --to-revisions REVISION_NAME=100
```

### Gradual Rollout

```bash
# Split traffic between revisions
gcloud run services update-traffic gateway \
  --region europe-west1 \
  --to-revisions REVISION_NEW=50,REVISION_OLD=50
```

---

## Advantages of Cloud Run vs Railway

### Pros
✅ **Better pricing for sporadic traffic** - Pay only for actual usage  
✅ **Scale to zero** - No cost when idle  
✅ **Native GCP integration** - Better monitoring, logging, IAM  
✅ **More control** - Fine-tune CPU, memory, concurrency  
✅ **Larger free tier** - 2M requests/month  
✅ **Better for enterprise** - VPC, IAM, compliance  

### Cons
❌ **More complex setup** - Requires gcloud CLI, GCP knowledge  
❌ **Cold starts** - First request after idle can be slow  
❌ **No built-in databases** - Must use external services  
❌ **Steeper learning curve** - More configuration options  

---

## Quick Reference Commands

```bash
# View all services
gcloud run services list --region europe-west1

# View logs
gcloud run logs read SERVICE_NAME --region europe-west1 --limit 100

# Update environment variable
gcloud run services update SERVICE_NAME \
  --region europe-west1 \
  --update-env-vars KEY=VALUE

# Update secret
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Scale service
gcloud run services update SERVICE_NAME \
  --region europe-west1 \
  --min-instances 1 \
  --max-instances 20

# View metrics
gcloud run services describe SERVICE_NAME --region europe-west1
```

---

## Next Steps

1. ✅ Install gcloud CLI
2. ✅ Set up GCP project
3. ✅ Create secrets
4. ✅ Build and push images
5. ✅ Deploy services
6. ✅ Deploy frontend
7. ✅ Run migrations
8. ✅ Seed data
9. ✅ Test end-to-end
10. ✅ Set up monitoring

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-11  
**Platform:** Google Cloud Run
