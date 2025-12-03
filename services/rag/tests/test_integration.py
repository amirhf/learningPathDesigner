"""
Integration tests for Deep Infra services
These tests require a valid DEEPINFRA_API_KEY environment variable

Run with: pytest tests/test_integration.py -v -s
"""
import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Skip all tests if no API key
pytestmark = pytest.mark.skipif(
    not os.environ.get("DEEPINFRA_API_KEY"),
    reason="DEEPINFRA_API_KEY not set"
)


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset all singletons before each test"""
    import embeddings
    import rerank
    import deepinfra_client
    from config import get_settings
    
    embeddings._embedding_service = None
    rerank._rerank_service = None
    deepinfra_client._client = None
    get_settings.cache_clear()
    
    yield
    
    # Cleanup after test
    embeddings._embedding_service = None
    rerank._rerank_service = None
    deepinfra_client._client = None
    get_settings.cache_clear()


class TestEmbeddingsIntegration:
    """Integration tests for embedding service"""
    
    def test_generate_single_embedding(self):
        """Test generating a single embedding"""
        from embeddings import get_embedding_service
        
        service = get_embedding_service()
        assert service.use_deepinfra is True
        
        embedding = service.generate_single_embedding("Hello, world!")
        
        assert isinstance(embedding, list)
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
    
    def test_generate_batch_embeddings(self):
        """Test generating embeddings for multiple texts"""
        from embeddings import get_embedding_service
        
        service = get_embedding_service()
        
        texts = [
            "Python is a programming language",
            "JavaScript is used for web development",
            "Machine learning with neural networks"
        ]
        
        embeddings = service.generate_embeddings(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
    
    def test_query_vs_passage_embeddings_differ(self):
        """Test that query and passage embeddings are different"""
        from embeddings import get_embedding_service
        
        service = get_embedding_service()
        text = "Python programming tutorial"
        
        query_emb = service.generate_single_embedding(text, instruction="query")
        passage_emb = service.generate_single_embedding(text, instruction="passage")
        
        # They should be different due to different prefixes
        assert query_emb != passage_emb
    
    def test_similar_texts_have_high_similarity(self):
        """Test that semantically similar texts have high cosine similarity"""
        import numpy as np
        from embeddings import get_embedding_service
        
        service = get_embedding_service()
        
        emb1 = service.generate_single_embedding("Python programming language")
        emb2 = service.generate_single_embedding("Python coding tutorial")
        emb3 = service.generate_single_embedding("Cooking pasta recipe")
        
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_related = cosine_similarity(emb1, emb2)
        sim_unrelated = cosine_similarity(emb1, emb3)
        
        print(f"\nSimilarity (Python vs Python tutorial): {sim_related:.4f}")
        print(f"Similarity (Python vs Cooking): {sim_unrelated:.4f}")
        
        assert sim_related > sim_unrelated
        assert sim_related > 0.8  # Related texts should be very similar


class TestRerankIntegration:
    """Integration tests for rerank service"""
    
    def test_rerank_orders_by_relevance(self):
        """Test that reranking orders documents by relevance"""
        from rerank import get_rerank_service
        
        service = get_rerank_service()
        assert service.use_deepinfra is True
        
        query = "Python programming tutorial"
        docs = [
            {"title": "Cooking Italian Pasta", "description": "Learn to make delicious pasta"},
            {"title": "Python Basics", "description": "Introduction to Python programming"},
            {"title": "JavaScript Web Dev", "description": "Building websites with JS"},
            {"title": "Advanced Python", "description": "Deep dive into Python features"},
        ]
        
        results, scores = service.rerank(query, docs, top_n=4)
        
        print("\nReranked results:")
        for doc, score in zip(results, scores):
            print(f"  {score:.4f} - {doc['title']}")
        
        # Python-related docs should be at the top
        assert "Python" in results[0]["title"]
        assert "Python" in results[1]["title"]
        # Cooking should be last
        assert "Cooking" in results[-1]["title"]
    
    def test_rerank_top_n_limit(self):
        """Test that top_n limits results correctly"""
        from rerank import get_rerank_service
        
        service = get_rerank_service()
        
        docs = [{"title": f"Doc {i}"} for i in range(10)]
        
        results, scores = service.rerank("test query", docs, top_n=3)
        
        assert len(results) == 3
        assert len(scores) == 3
    
    def test_rerank_scores_are_normalized(self):
        """Test that rerank scores are in expected range"""
        from rerank import get_rerank_service
        
        service = get_rerank_service()
        
        docs = [
            {"title": "Exact match query text"},
            {"title": "Something completely different"},
        ]
        
        results, scores = service.rerank("Exact match query text", docs, top_n=2)
        
        # Scores should be between 0 and 1 for Qwen reranker
        assert all(0 <= s <= 1 for s in scores)
        # The exact match should have higher score
        assert scores[0] > scores[1]


class TestEndToEnd:
    """End-to-end integration tests"""
    
    def test_embed_and_rerank_pipeline(self):
        """Test the full embed -> search -> rerank pipeline"""
        from embeddings import get_embedding_service
        from rerank import get_rerank_service
        import numpy as np
        
        embed_service = get_embedding_service()
        rerank_service = get_rerank_service()
        
        # Simulate document corpus
        corpus = [
            {"title": "Python Basics", "description": "Learn Python from scratch"},
            {"title": "Advanced Python", "description": "Master Python programming"},
            {"title": "JavaScript Intro", "description": "Web development basics"},
            {"title": "Machine Learning", "description": "ML with Python and TensorFlow"},
            {"title": "Cooking 101", "description": "Basic cooking techniques"},
        ]
        
        # 1. Embed corpus
        corpus_texts = [f"{d['title']} {d['description']}" for d in corpus]
        corpus_embeddings = embed_service.generate_embeddings(corpus_texts, instruction="passage")
        
        # 2. Embed query
        query = "How to learn Python programming"
        query_embedding = embed_service.generate_single_embedding(query, instruction="query")
        
        # 3. Find top candidates by cosine similarity
        def cosine_similarity(a, b):
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        similarities = [cosine_similarity(query_embedding, emb) for emb in corpus_embeddings]
        top_indices = np.argsort(similarities)[::-1][:3]  # Top 3
        candidates = [corpus[i] for i in top_indices]
        
        print("\nTop 3 by embedding similarity:")
        for i, idx in enumerate(top_indices):
            print(f"  {similarities[idx]:.4f} - {corpus[idx]['title']}")
        
        # 4. Rerank candidates
        reranked, scores = rerank_service.rerank(query, candidates, top_n=3)
        
        print("\nAfter reranking:")
        for doc, score in zip(reranked, scores):
            print(f"  {score:.4f} - {doc['title']}")
        
        # Verify Python docs are at the top
        assert "Python" in reranked[0]["title"]
