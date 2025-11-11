# Deployment Health Check Script
# Verifies all services are healthy and responding

param(
    [string]$GatewayUrl = "https://gateway.railway.app",
    [string]$RagUrl = "https://rag-service.railway.app",
    [string]$PlannerUrl = "https://planner-service.railway.app",
    [string]$QuizUrl = "https://quiz-service.railway.app",
    [string]$FrontendUrl = "https://your-app.vercel.app"
)

Write-Host "=== Deployment Health Check ===" -ForegroundColor Cyan
Write-Host ""

$allHealthy = $true

function Test-ServiceHealth {
    param(
        [string]$Name,
        [string]$Url
    )
    
    Write-Host "Checking $Name..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri "$Url/health" -Method Get -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            Write-Host " ✓ Healthy" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ✗ Unhealthy (Status: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-Frontend {
    param(
        [string]$Url
    )
    
    Write-Host "Checking Frontend..." -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method Get -TimeoutSec 10
        
        if ($response.StatusCode -eq 200) {
            Write-Host " ✓ Accessible" -ForegroundColor Green
            return $true
        } else {
            Write-Host " ✗ Inaccessible (Status: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host " ✗ Failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Check all services
Write-Host "Backend Services:" -ForegroundColor Yellow
$allHealthy = $allHealthy -and (Test-ServiceHealth "Gateway" $GatewayUrl)
$allHealthy = $allHealthy -and (Test-ServiceHealth "RAG Service" $RagUrl)
$allHealthy = $allHealthy -and (Test-ServiceHealth "Planner Service" $PlannerUrl)
$allHealthy = $allHealthy -and (Test-ServiceHealth "Quiz Service" $QuizUrl)

Write-Host ""
Write-Host "Frontend:" -ForegroundColor Yellow
$allHealthy = $allHealthy -and (Test-Frontend $FrontendUrl)

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan

if ($allHealthy) {
    Write-Host "All services are healthy! ✓" -ForegroundColor Green
    exit 0
} else {
    Write-Host "Some services are unhealthy! ✗" -ForegroundColor Red
    exit 1
}
