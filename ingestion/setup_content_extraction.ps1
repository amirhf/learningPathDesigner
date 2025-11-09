# Content Extraction Setup Script
# Prepares environment for Phase 4: Content Extraction

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Content Extraction Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"
$originalPath = Get-Location

# Step 1: Check Python
Write-Host "[1/5] Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Step 2: Install dependencies
Write-Host "`n[2/5] Installing Python dependencies..." -ForegroundColor Yellow
Set-Location "$PSScriptRoot"
try {
    pip install -r requirements.txt --quiet
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Some dependencies may have failed to install" -ForegroundColor Yellow
}

# Step 3: Check .env file
Write-Host "`n[3/5] Checking environment configuration..." -ForegroundColor Yellow
Set-Location $originalPath

$envFile = ".env"
$envExampleFile = ".env.example"

if (Test-Path $envFile) {
    Write-Host "  ✓ .env file exists" -ForegroundColor Green
    
    # Check for required S3 variables
    $envContent = Get-Content $envFile -Raw
    $hasAwsKey = $envContent -match "AWS_ACCESS_KEY_ID=.+"
    $hasAwsSecret = $envContent -match "AWS_SECRET_ACCESS_KEY=.+"
    $hasS3Bucket = $envContent -match "S3_BUCKET_NAME=.+"
    
    if ($hasAwsKey -and $hasAwsSecret -and $hasS3Bucket) {
        Write-Host "  ✓ S3 configuration found" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ S3 configuration incomplete" -ForegroundColor Yellow
        Write-Host "    Please add to .env:" -ForegroundColor Gray
        if (-not $hasAwsKey) { Write-Host "      AWS_ACCESS_KEY_ID=your_key" -ForegroundColor Gray }
        if (-not $hasAwsSecret) { Write-Host "      AWS_SECRET_ACCESS_KEY=your_secret" -ForegroundColor Gray }
        if (-not $hasS3Bucket) { Write-Host "      S3_BUCKET_NAME=learnpath-snippets" -ForegroundColor Gray }
    }
} else {
    Write-Host "  ⚠ .env file not found" -ForegroundColor Yellow
    Write-Host "    Creating from .env.example..." -ForegroundColor Gray
    Copy-Item $envExampleFile $envFile
    Write-Host "  ✓ Created .env file" -ForegroundColor Green
    Write-Host "    Please configure S3 settings in .env" -ForegroundColor Yellow
}

# Step 4: Test database connection
Write-Host "`n[4/5] Testing database connection..." -ForegroundColor Yellow
try {
    $dbTest = docker exec -i learnpath-postgres psql -U postgres -d learnpath -t -c "SELECT COUNT(*) FROM resource" 2>&1
    if ($LASTEXITCODE -eq 0) {
        $count = $dbTest.Trim()
        Write-Host "  ✓ Database connected" -ForegroundColor Green
        Write-Host "    Resources in database: $count" -ForegroundColor Gray
    } else {
        Write-Host "  ✗ Database connection failed" -ForegroundColor Red
        Write-Host "    Make sure Docker containers are running" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ✗ Database connection failed" -ForegroundColor Red
    Write-Host "    Make sure Docker containers are running" -ForegroundColor Yellow
}

# Step 5: Check S3 access (if configured)
Write-Host "`n[5/5] Checking S3 access..." -ForegroundColor Yellow

# Load .env file
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            if ($value -and $value -ne "") {
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
            }
        }
    }
}

$awsKey = $env:AWS_ACCESS_KEY_ID
$awsSecret = $env:AWS_SECRET_ACCESS_KEY
$s3Bucket = $env:S3_BUCKET_NAME

if ($awsKey -and $awsSecret -and $awsKey -ne "" -and $awsSecret -ne "") {
    Write-Host "  Testing S3 connection..." -ForegroundColor Gray
    
    # Create a simple Python script to test S3
    $testScript = @'
import boto3
import os
import sys

try:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1")
    )
    
    bucket = os.getenv("S3_BUCKET_NAME", "learnpath-snippets")
    
    # Try to list objects (or check if bucket exists)
    try:
        s3.head_bucket(Bucket=bucket)
        print("SUCCESS: Bucket accessible")
        sys.exit(0)
    except Exception as e:
        print("ERROR: " + str(e))
        sys.exit(1)
        
except Exception as e:
    print("ERROR: " + str(e))
    sys.exit(1)
'@
    
    $testScript | python 2>&1 | ForEach-Object {
        if ($_ -match "SUCCESS") {
            Write-Host "  ✓ S3 connection successful" -ForegroundColor Green
            Write-Host "    $_" -ForegroundColor Gray
        } elseif ($_ -match "BUCKET_NOT_FOUND") {
            Write-Host "  ⚠ $_" -ForegroundColor Yellow
        } elseif ($_ -match "ERROR") {
            Write-Host "  ✗ $_" -ForegroundColor Red
        } else {
            Write-Host "    $_" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  ⚠ S3 credentials not configured" -ForegroundColor Yellow
    Write-Host "    Add AWS credentials to .env to enable S3 upload" -ForegroundColor Gray
    Write-Host "`n    Options:" -ForegroundColor Cyan
    Write-Host "    1. Use AWS credentials (recommended for production)" -ForegroundColor White
    Write-Host "    2. Use LocalStack for local S3 testing" -ForegroundColor White
    Write-Host "    3. Skip S3 for now (store content locally)" -ForegroundColor White
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Setup Summary" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Configure S3 credentials in .env (if not done)" -ForegroundColor White
Write-Host "  2. Run: python -m ingestion.run_content_extraction --help" -ForegroundColor White
Write-Host "  3. Test with: python -m ingestion.run_content_extraction --limit 1 --dry-run" -ForegroundColor White
Write-Host ""

Set-Location $originalPath
