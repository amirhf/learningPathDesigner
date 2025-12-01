#!/bin/bash

# Database migration script
# Runs all SQL migrations in order

set -e

# Load environment variables
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
fi

# Default DATABASE_URL if not set
DATABASE_URL=${DATABASE_URL:-"postgresql://postgres:postgres@localhost:5432/learnpath"}

echo "Running migrations..."
echo "Database: $DATABASE_URL"

# Directory containing migrations
MIGRATIONS_DIR="shared/migrations"

# Check if migrations directory exists
if [ ! -d "$MIGRATIONS_DIR" ]; then
    echo "Error: Migrations directory not found: $MIGRATIONS_DIR"
    exit 1
fi

# Create migrations tracking table if it doesn't exist
psql "$DATABASE_URL" <<EOF
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT now()
);
EOF

# Run each migration file in order
for migration_file in $(ls $MIGRATIONS_DIR/*.sql | sort); do
    filename=$(basename "$migration_file")
    version="${filename%.*}"
    
    # Check if migration has already been applied
    already_applied=$(psql "$DATABASE_URL" -t -c "SELECT COUNT(*) FROM schema_migrations WHERE version = '$version';")
    
    if [ "$already_applied" -gt 0 ]; then
        echo "✓ $filename (already applied)"
    else
        echo "→ Applying $filename..."
        psql "$DATABASE_URL" -f "$migration_file"
        psql "$DATABASE_URL" -c "INSERT INTO schema_migrations (version) VALUES ('$version');"
        echo "✓ $filename (applied)"
    fi
done

echo ""
echo "All migrations completed successfully!"
