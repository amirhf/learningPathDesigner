# Deploy using Google Cloud Build (builds images in the cloud)
# This is much faster than building locally with slow internet

param(
    [string]$ProjectId = "learnpath-prod",
    [string]$Region = "europe-west1",
    [string]$AllowedOrigins = "https://your-app.vercel.app",
    [switch]$BuildOnly = $false
)

Write-Host "=== Cloud Build Deployment ===" -ForegroundColor Cyan
Write-Host "Project: $ProjectId"
Write-Host "Region: $Region"
Write-Host ""

# Check if gcloud is installed
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "Error: gcloud CLI not found. Please install it first." -ForegroundColor Red
    exit 1
}

# Set project
gcloud config set project $ProjectId

if ($BuildOnly) {
    Write-Host "Building images only (no deployment)..." -ForegroundColor Yellow
    Write-Host ""
    
    # Submit build job (images only)
    gcloud builds submit --config cloudbuild.yaml .
    
    Write-Host ""
    Write-Host "Build complete! Images pushed to GCR." -ForegroundColor Green
    Write-Host "To deploy, run: .\ops\cloud-build-deploy.ps1 -ProjectId $ProjectId"
} else {
    Write-Host "Building and deploying all services..." -ForegroundColor Yellow
    Write-Host ""
    
    # Submit build and deploy job
    gcloud builds submit `
        --config cloudbuild-deploy.yaml `
        --substitutions="_REGION=$Region,_ALLOWED_ORIGINS=$AllowedOrigins" `
        .
    
    Write-Host ""
    Write-Host "=== Deployment Complete! ===" -ForegroundColor Green
    Write-Host ""
    
    # Get service URLs
    Write-Host "Fetching service URLs..." -ForegroundColor Yellow
    $GATEWAY_URL = gcloud run services describe gateway --region $Region --format="value(status.url)"
    $RAG_URL = gcloud run services describe rag-service --region $Region --format="value(status.url)"
    $PLANNER_URL = gcloud run services describe planner-service --region $Region --format="value(status.url)"
    $QUIZ_URL = gcloud run services describe quiz-service --region $Region --format="value(status.url)"
    
    Write-Host ""
    Write-Host "Service URLs:" -ForegroundColor Cyan
    Write-Host "  Gateway:  $GATEWAY_URL" -ForegroundColor White
    Write-Host "  RAG:      $RAG_URL" -ForegroundColor White
    Write-Host "  Planner:  $PLANNER_URL" -ForegroundColor White
    Write-Host "  Quiz:     $QUIZ_URL" -ForegroundColor White
    Write-Host ""
    
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Update Vercel: NEXT_PUBLIC_API_URL=$GATEWAY_URL"
    Write-Host "2. Test health: curl $GATEWAY_URL/health"
    Write-Host "3. Visit your app!"
}

Write-Host ""
Write-Host "View build logs: https://console.cloud.google.com/cloud-build/builds?project=$ProjectId" -ForegroundColor Cyan
