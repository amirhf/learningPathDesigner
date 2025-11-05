FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables for model download
ENV EMBEDDING_MODEL=intfloat/e5-base-v2
ENV RERANKER_MODEL=BAAI/bge-reranker-base

# Download and cache models in the image
# This makes startup MUCH faster (2-3s vs 30-60s)
# Models are cached once during build, quantized at runtime
RUN python quantize_models.py

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
