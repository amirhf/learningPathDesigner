# Database migration script for Windows
# Runs all SQL migrations in order

$ErrorActionPreference = "Stop"

# Load environment variables from .env.local
if (Test-Path ".env.local") {
    Get-Content ".env.local" | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

# Default DATABASE_URL if not set
$DATABASE_URL = if ($env:DATABASE_URL) { $env:DATABASE_URL } else { "postgresql://postgres:postgres@localhost:5432/learnpath" }

Write-Host "Running migrations..." -ForegroundColor Cyan
Write-Host "Database: $DATABASE_URL" -ForegroundColor Gray

# Directory containing migrations
$MIGRATIONS_DIR = "shared/migrations"

# Check if migrations directory exists
if (-not (Test-Path $MIGRATIONS_DIR)) {
    Write-Host "Error: Migrations directory not found: $MIGRATIONS_DIR" -ForegroundColor Red
    exit 1
}

# Check if psql is available
try {
    $null = Get-Command psql -ErrorAction Stop
} catch {
    Write-Host "Error: psql command not found. Please install PostgreSQL client tools." -ForegroundColor Red
    exit 1
}

# Create migrations tracking table if it doesn't exist
$createTableSQL = @"
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT now()
);
"@

$createTableSQL | psql $DATABASE_URL 2>&1 | Out-Null

# Run each migration file in order
$migrationFiles = Get-ChildItem -Path $MIGRATIONS_DIR -Filter "*.sql" | Sort-Object Name

foreach ($migrationFile in $migrationFiles) {
    $filename = $migrationFile.Name
    $version = $migrationFile.BaseName
    
    # Check if migration has already been applied
    $checkSQL = "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';"
    $alreadyApplied = psql $DATABASE_URL -t -c $checkSQL 2>&1 | Out-String
    $alreadyApplied = $alreadyApplied.Trim()
    
    if ([int]$alreadyApplied -gt 0) {
        Write-Host "✓ $filename (already applied)" -ForegroundColor Green
    } else {
        Write-Host "→ Applying $filename..." -ForegroundColor Yellow
        psql $DATABASE_URL -f $migrationFile.FullName 2>&1 | Out-Null
        $insertSQL = "INSERT INTO schema_migrations (version) VALUES ('$version');"
        psql $DATABASE_URL -c $insertSQL 2>&1 | Out-Null
        Write-Host "✓ $filename (applied)" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "All migrations completed successfully!" -ForegroundColor Green
