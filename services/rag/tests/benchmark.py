#!/usr/bin/env python3
"""
Performance benchmarks for Deep Infra services

Run with: python tests/benchmark.py
"""
import time
import statistics
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def benchmark_embeddings(n_iterations: int = 20, batch_sizes: list = [1, 5, 10]):
    """Benchmark embedding generation latency"""
    from embeddings import get_embedding_service
    
    service = get_embedding_service()
    print(f"\n{'='*60}")
    print("EMBEDDING BENCHMARK")
    print(f"{'='*60}")
    print(f"Using Deep Infra: {service.use_deepinfra}")
    print(f"Iterations per batch size: {n_iterations}")
    
    for batch_size in batch_sizes:
        texts = [f"Sample text number {i} for embedding generation test" for i in range(batch_size)]
        latencies = []
        
        # Warmup
        service.generate_embeddings(texts[:1])
        
        for _ in range(n_iterations):
            start = time.perf_counter()
            service.generate_embeddings(texts)
            latencies.append((time.perf_counter() - start) * 1000)
        
        print(f"\nBatch size: {batch_size}")
        print(f"  Mean:   {statistics.mean(latencies):>8.2f} ms")
        print(f"  Median: {statistics.median(latencies):>8.2f} ms")
        print(f"  Std:    {statistics.stdev(latencies):>8.2f} ms")
        print(f"  Min:    {min(latencies):>8.2f} ms")
        print(f"  Max:    {max(latencies):>8.2f} ms")
        print(f"  P95:    {sorted(latencies)[int(n_iterations * 0.95)]:>8.2f} ms")


def benchmark_rerank(n_iterations: int = 20, doc_counts: list = [3, 5, 10, 20]):
    """Benchmark reranking latency"""
    from rerank import get_rerank_service
    
    service = get_rerank_service()
    print(f"\n{'='*60}")
    print("RERANK BENCHMARK")
    print(f"{'='*60}")
    print(f"Using Deep Infra: {service.use_deepinfra}")
    print(f"Iterations per doc count: {n_iterations}")
    
    query = "Python programming tutorial for beginners"
    
    for doc_count in doc_counts:
        docs = [
            {"title": f"Document {i}", "description": f"This is document number {i} with some content"}
            for i in range(doc_count)
        ]
        latencies = []
        
        # Warmup
        service.rerank(query, docs[:3], top_n=3)
        
        for _ in range(n_iterations):
            start = time.perf_counter()
            service.rerank(query, docs, top_n=min(5, doc_count))
            latencies.append((time.perf_counter() - start) * 1000)
        
        print(f"\nDocument count: {doc_count}")
        print(f"  Mean:   {statistics.mean(latencies):>8.2f} ms")
        print(f"  Median: {statistics.median(latencies):>8.2f} ms")
        print(f"  Std:    {statistics.stdev(latencies):>8.2f} ms")
        print(f"  Min:    {min(latencies):>8.2f} ms")
        print(f"  Max:    {max(latencies):>8.2f} ms")
        print(f"  P95:    {sorted(latencies)[int(n_iterations * 0.95)]:>8.2f} ms")


def benchmark_full_pipeline(n_iterations: int = 10):
    """Benchmark full search pipeline (embed query + rerank)"""
    from embeddings import get_embedding_service
    from rerank import get_rerank_service
    
    embed_service = get_embedding_service()
    rerank_service = get_rerank_service()
    
    print(f"\n{'='*60}")
    print("FULL PIPELINE BENCHMARK (embed + rerank)")
    print(f"{'='*60}")
    print(f"Iterations: {n_iterations}")
    
    query = "How to learn Python programming"
    docs = [
        {"title": "Python Basics", "description": "Learn Python from scratch"},
        {"title": "Advanced Python", "description": "Master Python programming"},
        {"title": "JavaScript Intro", "description": "Web development basics"},
        {"title": "Machine Learning", "description": "ML with Python and TensorFlow"},
        {"title": "Cooking 101", "description": "Basic cooking techniques"},
    ]
    
    embed_latencies = []
    rerank_latencies = []
    total_latencies = []
    
    # Warmup
    embed_service.generate_single_embedding("warmup", instruction="query")
    rerank_service.rerank("warmup", docs[:2], top_n=2)
    
    for _ in range(n_iterations):
        total_start = time.perf_counter()
        
        # Embed query
        embed_start = time.perf_counter()
        query_embedding = embed_service.generate_single_embedding(query, instruction="query")
        embed_latencies.append((time.perf_counter() - embed_start) * 1000)
        
        # Rerank (assuming candidates already retrieved from vector DB)
        rerank_start = time.perf_counter()
        results, scores = rerank_service.rerank(query, docs, top_n=3)
        rerank_latencies.append((time.perf_counter() - rerank_start) * 1000)
        
        total_latencies.append((time.perf_counter() - total_start) * 1000)
    
    print(f"\nEmbed Query:")
    print(f"  Mean: {statistics.mean(embed_latencies):.2f} ms")
    print(f"  P95:  {sorted(embed_latencies)[int(n_iterations * 0.95)]:.2f} ms")
    
    print(f"\nRerank (5 docs):")
    print(f"  Mean: {statistics.mean(rerank_latencies):.2f} ms")
    print(f"  P95:  {sorted(rerank_latencies)[int(n_iterations * 0.95)]:.2f} ms")
    
    print(f"\nTotal Pipeline:")
    print(f"  Mean: {statistics.mean(total_latencies):.2f} ms")
    print(f"  P95:  {sorted(total_latencies)[int(n_iterations * 0.95)]:.2f} ms")


def main():
    """Run all benchmarks"""
    print("\n" + "="*60)
    print("DEEP INFRA PERFORMANCE BENCHMARKS")
    print("="*60)
    
    # Check API key
    from config import get_settings
    settings = get_settings()
    
    if not settings.deepinfra_api_key:
        print("ERROR: DEEPINFRA_API_KEY not set")
        sys.exit(1)
    
    print(f"\nAPI Base URL: {settings.deepinfra_base_url}")
    print(f"Embedding Model: {settings.deepinfra_embedding_model}")
    print(f"Reranker Model: {settings.deepinfra_reranker_model}")
    
    try:
        benchmark_embeddings(n_iterations=20)
        benchmark_rerank(n_iterations=20)
        benchmark_full_pipeline(n_iterations=10)
        
        print("\n" + "="*60)
        print("BENCHMARKS COMPLETE")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
