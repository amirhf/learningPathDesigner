# Google Cloud Run Deployment Script (PowerShell)
# Builds and deploys all services to Cloud Run

param(
    [string]$ProjectId = "learnpath-prod",
    [string]$Region = "europe-west1"
)

Write-Host "=== Learning Path Designer - Cloud Run Deployment ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host ""

# Check if gcloud is installed
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI not found. Please install it first." -ForegroundColor Red
    Write-Host "https://cloud.google.com/sdk/docs/install"
    exit 1
}

# Set project
gcloud config set project $ProjectId

Write-Host "Step 1: Building Docker images..." -ForegroundColor Yellow
Write-Host ""

# Build RAG Service
Write-Host "Building RAG service..."
Set-Location services\rag
docker build -t gcr.io/$ProjectId/rag-service:latest .
docker push gcr.io/$ProjectId/rag-service:latest
Set-Location ..\..

# Build Planner Service
Write-Host "Building Planner service..."
Set-Location services\planner
docker build -t gcr.io/$ProjectId/planner-service:latest .
docker push gcr.io/$ProjectId/planner-service:latest
Set-Location ..\..

# Build Quiz Service
Write-Host "Building Quiz service..."
Set-Location services\quiz
docker build -t gcr.io/$ProjectId/quiz-service:latest .
docker push gcr.io/$ProjectId/quiz-service:latest
Set-Location ..\..

# Build Gateway
Write-Host "Building Gateway..."
Set-Location gateway
docker build -t gcr.io/$ProjectId/gateway:latest .
docker push gcr.io/$ProjectId/gateway:latest
Set-Location ..

Write-Host ""
Write-Host "Step 2: Deploying services to Cloud Run..." -ForegroundColor Yellow
Write-Host ""

# Deploy RAG Service
Write-Host "Deploying RAG service..."
gcloud run deploy rag-service `
  --image gcr.io/$ProjectId/rag-service:latest `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --concurrency 10 `
  --min-instances 0 `
  --max-instances 10 `
  --quiet

$RAG_URL = gcloud run services describe rag-service --region $Region --format="value(status.url)"
Write-Host "✓ RAG Service deployed: $RAG_URL" -ForegroundColor Green

# Deploy Planner Service
Write-Host "Deploying Planner service..."
gcloud run deploy planner-service `
  --image gcr.io/$ProjectId/planner-service:latest `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --timeout 300 `
  --concurrency 20 `
  --min-instances 0 `
  --max-instances 10 `
  --update-env-vars="RAG_SERVICE_URL=$RAG_URL" `
  --quiet

$PLANNER_URL = gcloud run services describe planner-service --region $Region --format="value(status.url)"
Write-Host "✓ Planner Service deployed: $PLANNER_URL" -ForegroundColor Green

# Deploy Quiz Service
Write-Host "Deploying Quiz service..."
gcloud run deploy quiz-service `
  --image gcr.io/$ProjectId/quiz-service:latest `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --timeout 300 `
  --concurrency 20 `
  --min-instances 0 `
  --max-instances 10 `
  --quiet

$QUIZ_URL = gcloud run services describe quiz-service --region $Region --format="value(status.url)"
Write-Host "✓ Quiz Service deployed: $QUIZ_URL" -ForegroundColor Green

# Deploy Gateway
Write-Host "Deploying Gateway..."
gcloud run deploy gateway `
  --image gcr.io/$ProjectId/gateway:latest `
  --platform managed `
  --region $Region `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --timeout 60 `
  --concurrency 80 `
  --min-instances 0 `
  --max-instances 20 `
  --update-env-vars="RAG_SERVICE_URL=$RAG_URL,PLANNER_SERVICE_URL=$PLANNER_URL,QUIZ_SERVICE_URL=$QUIZ_URL" `
  --quiet

$GATEWAY_URL = gcloud run services describe gateway --region $Region --format="value(status.url)"
Write-Host "✓ Gateway deployed: $GATEWAY_URL" -ForegroundColor Green

Write-Host ""
Write-Host "=== Deployment Complete! ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "  Gateway:  $GATEWAY_URL"
Write-Host "  RAG:      $RAG_URL"
Write-Host "  Planner:  $PLANNER_URL"
Write-Host "  Quiz:     $QUIZ_URL"
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update Vercel environment variable: NEXT_PUBLIC_API_URL=$GATEWAY_URL"
Write-Host "2. Update Gateway CORS: gcloud run services update gateway --region $Region --update-env-vars=`"ALLOWED_ORIGINS=https://your-app.vercel.app`""
Write-Host "3. Run health checks: curl $GATEWAY_URL/health"
Write-Host ""
