#!/bin/bash
# Deploy using Google Cloud Build (builds images in the cloud)
# This is much faster than building locally with slow internet

set -e

PROJECT_ID="${GCP_PROJECT_ID:-learnpath-prod}"
REGION="${GCP_REGION:-europe-west1}"
ALLOWED_ORIGINS="${ALLOWED_ORIGINS:-https://your-app.vercel.app}"
BUILD_ONLY="${BUILD_ONLY:-false}"

echo "=== Cloud Build Deployment ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Please install it first."
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID

if [ "$BUILD_ONLY" = "true" ]; then
    echo "Building images only (no deployment)..."
    echo ""
    
    # Submit build job (images only)
    gcloud builds submit --config cloudbuild.yaml .
    
    echo ""
    echo "Build complete! Images pushed to GCR."
    echo "To deploy, run: ./ops/cloud-build-deploy.sh"
else
    echo "Building and deploying all services..."
    echo ""
    
    # Submit build and deploy job
    gcloud builds submit \
        --config cloudbuild-deploy.yaml \
        --substitutions="_REGION=$REGION,_ALLOWED_ORIGINS=$ALLOWED_ORIGINS" \
        .
    
    echo ""
    echo "=== Deployment Complete! ==="
    echo ""
    
    # Get service URLs
    echo "Fetching service URLs..."
    GATEWAY_URL=$(gcloud run services describe gateway --region $REGION --format="value(status.url)")
    RAG_URL=$(gcloud run services describe rag-service --region $REGION --format="value(status.url)")
    PLANNER_URL=$(gcloud run services describe planner-service --region $REGION --format="value(status.url)")
    QUIZ_URL=$(gcloud run services describe quiz-service --region $REGION --format="value(status.url)")
    
    echo ""
    echo "Service URLs:"
    echo "  Gateway:  $GATEWAY_URL"
    echo "  RAG:      $RAG_URL"
    echo "  Planner:  $PLANNER_URL"
    echo "  Quiz:     $QUIZ_URL"
    echo ""
    
    echo "Next steps:"
    echo "1. Update Vercel: NEXT_PUBLIC_API_URL=$GATEWAY_URL"
    echo "2. Test health: curl $GATEWAY_URL/health"
    echo "3. Visit your app!"
fi

echo ""
echo "View build logs: https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID"
