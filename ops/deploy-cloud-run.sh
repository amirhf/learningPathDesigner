#!/bin/bash
# Google Cloud Run Deployment Script
# Builds and deploys all services to Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-learnpath-prod}"
REGION="${GCP_REGION:-europe-west1}"

echo "=== Learning Path Designer - Cloud Run Deployment ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it first."
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if logged in
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "Error: Not logged in to gcloud. Run: gcloud auth login"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

echo "Step 1: Building Docker images..."
echo ""

# Build RAG Service
echo "Building RAG service..."
cd services/rag
docker build -t gcr.io/$PROJECT_ID/rag-service:latest .
docker push gcr.io/$PROJECT_ID/rag-service:latest
cd ../..

# Build Planner Service
echo "Building Planner service..."
cd services/planner
docker build -t gcr.io/$PROJECT_ID/planner-service:latest .
docker push gcr.io/$PROJECT_ID/planner-service:latest
cd ../..

# Build Quiz Service
echo "Building Quiz service..."
cd services/quiz
docker build -t gcr.io/$PROJECT_ID/quiz-service:latest .
docker push gcr.io/$PROJECT_ID/quiz-service:latest
cd ../..

# Build Gateway
echo "Building Gateway..."
cd gateway
docker build -t gcr.io/$PROJECT_ID/gateway:latest .
docker push gcr.io/$PROJECT_ID/gateway:latest
cd ..

echo ""
echo "Step 2: Deploying services to Cloud Run..."
echo ""

# Deploy RAG Service
echo "Deploying RAG service..."
gcloud run deploy rag-service \
  --image gcr.io/$PROJECT_ID/rag-service:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --concurrency 10 \
  --min-instances 0 \
  --max-instances 10 \
  --quiet

RAG_URL=$(gcloud run services describe rag-service --region $REGION --format="value(status.url)")
echo "✓ RAG Service deployed: $RAG_URL"

# Deploy Planner Service
echo "Deploying Planner service..."
gcloud run deploy planner-service \
  --image gcr.io/$PROJECT_ID/planner-service:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 20 \
  --min-instances 0 \
  --max-instances 10 \
  --update-env-vars="RAG_SERVICE_URL=$RAG_URL" \
  --quiet

PLANNER_URL=$(gcloud run services describe planner-service --region $REGION --format="value(status.url)")
echo "✓ Planner Service deployed: $PLANNER_URL"

# Deploy Quiz Service
echo "Deploying Quiz service..."
gcloud run deploy quiz-service \
  --image gcr.io/$PROJECT_ID/quiz-service:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --concurrency 20 \
  --min-instances 0 \
  --max-instances 10 \
  --quiet

QUIZ_URL=$(gcloud run services describe quiz-service --region $REGION --format="value(status.url)")
echo "✓ Quiz Service deployed: $QUIZ_URL"

# Deploy Gateway
echo "Deploying Gateway..."
gcloud run deploy gateway \
  --image gcr.io/$PROJECT_ID/gateway:latest \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --concurrency 80 \
  --min-instances 0 \
  --max-instances 20 \
  --update-env-vars="RAG_SERVICE_URL=$RAG_URL,PLANNER_SERVICE_URL=$PLANNER_URL,QUIZ_SERVICE_URL=$QUIZ_URL" \
  --quiet

GATEWAY_URL=$(gcloud run services describe gateway --region $REGION --format="value(status.url)")
echo "✓ Gateway deployed: $GATEWAY_URL"

echo ""
echo "=== Deployment Complete! ==="
echo ""
echo "Service URLs:"
echo "  Gateway:  $GATEWAY_URL"
echo "  RAG:      $RAG_URL"
echo "  Planner:  $PLANNER_URL"
echo "  Quiz:     $QUIZ_URL"
echo ""
echo "Next steps:"
echo "1. Update Vercel environment variable: NEXT_PUBLIC_API_URL=$GATEWAY_URL"
echo "2. Update Gateway CORS: gcloud run services update gateway --region $REGION --update-env-vars=\"ALLOWED_ORIGINS=https://your-app.vercel.app\""
echo "3. Run health checks: curl $GATEWAY_URL/health"
echo ""
