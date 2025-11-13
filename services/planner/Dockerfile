FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
# Local: uses port from config (8002)
# Cloud Run: set PORT=8080 env var to override
EXPOSE 8002 8080

# Run the application
# Uses PORT env var if set, otherwise falls back to config default (8002)
CMD ["sh", "-c", "echo 'Starting uvicorn on port '${PORT:-8002} && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8002}"]
