# Helper script to run commands with virtual environment activated
# Usage: .\run-with-venv.ps1 "python -m ingestion.seed_skills"

param(
    [Parameter(Mandatory=$true)]
    [string]$Command
)

$ErrorActionPreference = "Stop"

# Check if venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "[ERROR] Virtual environment not found. Run setup.ps1 first." -ForegroundColor Red
    exit 1
}

# Activate venv and run command
& .\.venv\Scripts\Activate.ps1
Invoke-Expression $Command
