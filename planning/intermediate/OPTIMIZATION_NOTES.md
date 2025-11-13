# Optimization Notes

## Model Loading Optimization

### Current Behavior
On first run, the RAG service downloads models from Hugging Face:
- **e5-base-v2**: ~400MB (embedding model)
- **bge-reranker-base**: ~1.1GB (reranking model)
- **Total**: ~1.5GB download
- **First startup time**: ~2 minutes

### Solutions Implemented

#### 1. Local Development
**Preload script**: `services/rag/preload_models.py`

Run once to cache models locally:
```bash
cd services/rag
python preload_models.py
```

Models are cached in `~/.cache/huggingface/hub/` and reused on subsequent runs.

**Subsequent startup time**: ~10 seconds

#### 2. Docker/Production
**Dockerfile optimization**: Models are preloaded during image build

```dockerfile
RUN python preload_models.py
```

This caches models in the Docker image, so containers start instantly.

**Benefits**:
- No download on container startup
- Predictable startup time
- Works offline after build

**Trade-off**: Docker image is ~2GB larger

### Future Optimizations (Phase 4+)

#### Option 1: Model Quantization
Reduce model size by 4x with minimal accuracy loss:

```python
# Use quantized models
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"  # 80MB vs 400MB
reranker_model = "cross-encoder/ms-marco-MiniLM-L-6-v2"     # 90MB vs 1.1GB
```

**Pros**: Much faster download, less memory
**Cons**: Slightly lower accuracy (~2-3%)

#### Option 2: Lazy Loading
Load reranker only when needed:

```python
# Load reranker on first rerank request
if request.rerank and not reranker_loaded:
    load_reranker()
```

**Pros**: Faster startup if reranking not used
**Cons**: First rerank request is slow

#### Option 3: Model Server
Separate model serving from API:

```
┌──────────┐      ┌──────────────┐
│ API      │─────▶│ Model Server │
│ (FastAPI)│      │ (Triton/TF)  │
└──────────┘      └──────────────┘
```

**Pros**: Scale models independently, GPU optimization
**Cons**: More complex architecture

#### Option 4: CDN for Models
Host models on CDN for faster downloads:

```bash
export HF_ENDPOINT=https://your-cdn.com/models
```

**Pros**: Faster downloads in production regions
**Cons**: Additional infrastructure cost

## Recommended Approach

### Phase 1 (Current)
✅ Preload models in Docker image
- Simple, works well for Railway/Fly.io
- Acceptable image size (~2GB)

### Phase 2-3
Continue with current approach, monitor:
- Startup time
- Memory usage
- Search latency

### Phase 4 (If needed)
Consider optimizations if:
- Image size becomes problematic (>3GB)
- Startup time >30s
- Memory usage >4GB
- Search latency >500ms

Then evaluate:
1. **Quantized models** (easiest, 80% size reduction)
2. **Model server** (if scaling issues)
3. **CDN** (if download speed is bottleneck)

## Performance Targets

| Metric | Current | Target (Phase 4) |
|--------|---------|------------------|
| Docker image size | 2GB | <1GB |
| Cold start | 10s | <5s |
| Search latency | 200-300ms | <100ms |
| Memory usage | 2GB | <1GB |
| Throughput | 10 req/s | 50 req/s |

## Monitoring

Track these metrics in production:
- Model load time
- Search latency (p50, p95, p99)
- Memory usage
- Cache hit rate
- Error rate

Add to Phase 4 observability setup.

## Notes

- Models are cached per environment (dev, staging, prod)
- Cache is persistent in Docker volumes
- First deployment to new region will download models
- Consider warming up cache in CI/CD pipeline

## References

- [Hugging Face Model Optimization](https://huggingface.co/docs/optimum/index)
- [ONNX Runtime](https://onnxruntime.ai/)
- [Model Quantization Guide](https://huggingface.co/docs/transformers/main/en/quantization)
