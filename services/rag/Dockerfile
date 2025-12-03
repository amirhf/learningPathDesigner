# Use multi-stage build for smaller final image
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Copy pre-downloaded models (if available in build context)
COPY models_cache /app/models_cache

# Run model quantization/download script
# This script saves models to /app/models
RUN python quantize_models.py

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Copy prepared models from builder
COPY --from=builder /app/models /app/models

# Set environment variables to use local models
ENV EMBEDDING_MODEL=/app/models/embedding
ENV RERANKER_MODEL=/app/models/reranker

EXPOSE 8001 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8001}"]
