# Quick Deployment with Cloud Build

**⚡ Fast deployment for slow internet connections**

Cloud Build builds your Docker images in Google's cloud infrastructure, eliminating the need to upload large images (2-3GB) from your local machine.

---

## Why Use Cloud Build?

### Without Cloud Build (Local Build)
1. Build Docker images locally (~10 min)
2. Upload to GCR with slow internet (~30-60 min) ❌
3. Deploy to Cloud Run (~10 min)
**Total: 50-80 minutes**

### With Cloud Build
1. Upload source code (~1-2 min) ✅
2. Build in cloud with fast network (~8-10 min) ✅
3. Auto-deploy to Cloud Run (~5 min) ✅
**Total: 15-20 minutes**

---

## Prerequisites

1. **Google Cloud Project** created
2. **gcloud CLI** installed and authenticated
3. **Cloud Build API** enabled
4. **Secrets** created in Secret Manager

---

## One-Command Deployment

### PowerShell (Windows)

```powershell
# Build and deploy everything
.\ops\cloud-build-deploy.ps1 -ProjectId "learnpath-prod" -Region "europe-west1"

# Build only (no deployment)
.\ops\cloud-build-deploy.ps1 -BuildOnly
```

### Bash (Linux/Mac)

```bash
# Build and deploy everything
./ops/cloud-build-deploy.sh

# Build only (no deployment)
BUILD_ONLY=true ./ops/cloud-build-deploy.sh
```

---

## Step-by-Step Guide

### Step 1: Enable Cloud Build API

```bash
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Grant Cloud Build Permissions

Cloud Build needs permission to deploy to Cloud Run:

```bash
# Get project number
$PROJECT_NUMBER=$(gcloud projects describe learnpath-prod --format="value(projectNumber)")

# Grant Cloud Run Admin role to Cloud Build
gcloud projects add-iam-policy-binding learnpath-prod `
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" `
  --role="roles/run.admin"

# Grant Service Account User role
gcloud projects add-iam-policy-binding learnpath-prod `
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" `
  --role="roles/iam.serviceAccountUser"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding learnpath-prod `
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

### Step 3: Submit Build

**Option A: Build and Deploy (Recommended)**

```bash
gcloud builds submit `
  --config cloudbuild-deploy.yaml `
  --substitutions="_REGION=europe-west1,_ALLOWED_ORIGINS=https://your-app.vercel.app" `
  .
```

**Option B: Build Only**

```bash
gcloud builds submit --config cloudbuild.yaml .
```

Then deploy manually later (see Phase 4 in main deployment plan).

### Step 4: Monitor Build Progress

**View in Console:**
```
https://console.cloud.google.com/cloud-build/builds?project=learnpath-prod
```

**View logs in terminal:**
```bash
# Get latest build ID
BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)")

# Stream logs
gcloud builds log $BUILD_ID --stream
```

### Step 5: Get Service URLs

After deployment completes:

```bash
# Gateway URL
gcloud run services describe gateway --region europe-west1 --format="value(status.url)"

# All service URLs
gcloud run services list --region europe-west1
```

---

## Configuration Files

### `cloudbuild.yaml` - Build Only

Builds all Docker images and pushes to GCR. Does not deploy.

**Use case:** Build images first, deploy later manually.

### `cloudbuild-deploy.yaml` - Build + Deploy

Builds images AND deploys to Cloud Run in one step.

**Use case:** Complete deployment in one command.

---

## Build Configuration

### Machine Type

Default: `E2_HIGHCPU_8` (8 vCPUs, 8GB RAM)

For faster builds, you can use a larger machine:

```yaml
options:
  machineType: 'E2_HIGHCPU_32'  # 32 vCPUs, 32GB RAM
```

**Cost:** ~$0.11/min for E2_HIGHCPU_8 (first 120 min/day free)

### Timeout

Default: 30 minutes (1800s)

RAG service has large ML models, so we set a generous timeout.

### Parallel Builds

Cloud Build automatically builds services in parallel when possible, making it much faster than sequential local builds.

---

## Troubleshooting

### Error: "Permission denied"

**Solution:** Grant Cloud Build permissions (see Step 2 above)

### Error: "API not enabled"

**Solution:**
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Error: "Timeout"

**Solution:** Increase timeout in `cloudbuild.yaml`:
```yaml
timeout: '3600s'  # 60 minutes
```

### Build is slow

**Solution:** Use a larger machine type:
```yaml
options:
  machineType: 'E2_HIGHCPU_32'
```

### Want to see detailed logs

**Solution:**
```bash
# Stream logs during build
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)") --stream

# View in Cloud Console
https://console.cloud.google.com/cloud-build/builds
```

---

## Cost Breakdown

### Cloud Build Pricing

**Free Tier:**
- 120 build-minutes per day
- After that: ~$0.003/build-minute

**Typical Build Times:**
- RAG service: ~8 minutes
- Planner service: ~3 minutes
- Quiz service: ~3 minutes
- Gateway: ~2 minutes
- **Total: ~16 minutes**

**Cost for one deployment:**
- Within free tier: $0
- After free tier: ~$0.05

**Monthly cost (5 deployments/day):**
- ~$7.50/month (if exceeding free tier)

---

## CI/CD Integration

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
      
      - name: Deploy
        run: |
          gcloud builds submit \
            --config cloudbuild-deploy.yaml \
            --substitutions="_REGION=europe-west1,_ALLOWED_ORIGINS=${{ secrets.VERCEL_URL }}" \
            .
```

---

## Advantages Summary

✅ **Fast** - No need to upload large images  
✅ **Reliable** - Google's infrastructure  
✅ **Parallel** - Builds services simultaneously  
✅ **Integrated** - Works with Cloud Run, Secret Manager  
✅ **Logged** - Complete build logs in Cloud Console  
✅ **Affordable** - 120 free minutes/day  
✅ **Automated** - Can trigger from GitHub, Cloud Source Repos  

---

## Next Steps

1. ✅ Run `.\ops\cloud-build-deploy.ps1`
2. ✅ Wait ~15-20 minutes for build and deployment
3. ✅ Get Gateway URL
4. ✅ Update Vercel with Gateway URL
5. ✅ Test your app!

---

## Quick Reference

```bash
# Full deployment
gcloud builds submit --config cloudbuild-deploy.yaml .

# Build only
gcloud builds submit --config cloudbuild.yaml .

# View builds
gcloud builds list

# View logs
gcloud builds log BUILD_ID --stream

# Cancel build
gcloud builds cancel BUILD_ID
```

---

**For detailed deployment instructions, see:**
- `planning/DEPLOYMENT_PLAN_CLOUD_RUN.md` - Complete deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Step-by-step checklist
