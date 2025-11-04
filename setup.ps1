# Setup script for Learning Path Designer
# Run this script to set up your local development environment

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Learning Path Designer - Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "[OK] Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "[OK] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Python not found. Please install Python 3.11+." -ForegroundColor Red
    exit 1
}

# Check Go
if (Get-Command go -ErrorAction SilentlyContinue) {
    $goVersion = go version
    Write-Host "[OK] Go: $goVersion" -ForegroundColor Green
} else {
    Write-Host "[WARN] Go not found. Install Go 1.21+ to run gateway." -ForegroundColor Yellow
}

# Check Node
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "[OK] Node: $nodeVersion" -ForegroundColor Green
} else {
    Write-Host "[WARN] Node.js not found. Install Node.js 20+ to run frontend." -ForegroundColor Yellow
}

# Check PostgreSQL client
if (Get-Command psql -ErrorAction SilentlyContinue) {
    $psqlVersion = psql --version
    Write-Host "[OK] PostgreSQL client: $psqlVersion" -ForegroundColor Green
} else {
    Write-Host "[WARN] psql not found. Install PostgreSQL client tools." -ForegroundColor Yellow
}

Write-Host ""

# Create .env.local if it doesn't exist
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating .env.local from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env.local"
    Write-Host "[OK] Created .env.local" -ForegroundColor Green
    Write-Host "[WARN] Please update .env.local with your API keys" -ForegroundColor Yellow
} else {
    Write-Host "[OK] .env.local already exists" -ForegroundColor Green
}

Write-Host ""

# Start Docker services
Write-Host "Starting Docker services..." -ForegroundColor Yellow
docker-compose up -d

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check if services are running
$postgresRunning = docker ps --filter "name=learnpath-postgres" --filter "status=running" -q
$qdrantRunning = docker ps --filter "name=learnpath-qdrant" --filter "status=running" -q
$redisRunning = docker ps --filter "name=learnpath-redis" --filter "status=running" -q

if ($postgresRunning) {
    Write-Host "[OK] Postgres is running" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Postgres failed to start" -ForegroundColor Red
}

if ($qdrantRunning) {
    Write-Host "[OK] Qdrant is running" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Qdrant failed to start" -ForegroundColor Red
}

if ($redisRunning) {
    Write-Host "[OK] Redis is running" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Redis failed to start" -ForegroundColor Red
}

Write-Host ""

# Run migrations
if (Get-Command psql -ErrorAction SilentlyContinue) {
    Write-Host "Running database migrations..." -ForegroundColor Yellow
    Start-Sleep -Seconds 3
    try {
        .\ops\migrate.ps1
        Write-Host "[OK] Migrations completed" -ForegroundColor Green
    } catch {
        Write-Host "[WARN] Migrations failed. Run manually: .\ops\migrate.ps1" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] Skipping migrations (psql not found)" -ForegroundColor Yellow
}

Write-Host ""

# Setup virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "[OK] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[OK] Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    & .\.venv\Scripts\Activate.ps1
    pip install -r ingestion/requirements.txt --quiet
    Write-Host "[OK] Python dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Failed to install Python dependencies" -ForegroundColor Yellow
}

Write-Host ""

# Seed skills
Write-Host "Seeding skills data..." -ForegroundColor Yellow
try {
    & .\.venv\Scripts\python.exe -m ingestion.seed_skills
    Write-Host "[OK] Skills seeded" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Failed to seed skills" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update .env.local with your API keys" -ForegroundColor White
Write-Host "2. Review planning/implementation_steps.md" -ForegroundColor White
Write-Host "3. Start building Phase 1" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Yellow
Write-Host "  docker-compose ps" -ForegroundColor White
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
