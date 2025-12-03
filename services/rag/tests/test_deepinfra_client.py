"""
Unit tests for Deep Infra client
"""
import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reset_modules():
    """Reset all module singletons and caches"""
    import deepinfra_client
    import embeddings
    import rerank
    from config import get_settings
    
    deepinfra_client._client = None
    embeddings._embedding_service = None
    rerank._rerank_service = None
    get_settings.cache_clear()


class TestDeepInfraClient:
    """Tests for DeepInfraClient"""
    
    def test_client_requires_api_key(self):
        """Test that client raises error without API key"""
        reset_modules()
        
        with patch.dict(os.environ, {"USE_DEEPINFRA": "true", "DEEPINFRA_API_KEY": ""}, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            from deepinfra_client import DeepInfraClient
            with pytest.raises(ValueError, match="DEEPINFRA_API_KEY is required"):
                DeepInfraClient()
    
    def test_embeddings_api_call(self):
        """Test embedding generation makes correct API call"""
        reset_modules()
        
        # Patch environment BEFORE importing/creating client
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            with patch('deepinfra_client.httpx.Client') as mock_client:
                # Setup mock response
                mock_response = MagicMock()
                mock_response.json.return_value = {
                    "embeddings": [[0.1, 0.2, 0.3] * 256]  # 768 dimensions
                }
                mock_response.raise_for_status = MagicMock()
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                
                from deepinfra_client import DeepInfraClient
                client = DeepInfraClient()
                result = client.generate_embeddings_sync(["test text"])
                
                assert len(result) == 1
                assert len(result[0]) == 768
    
    def test_rerank_api_call(self):
        """Test reranking makes correct API call"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            with patch('deepinfra_client.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = {"scores": [0.95, 0.80, 0.60]}
                mock_response.raise_for_status = MagicMock()
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                
                from deepinfra_client import DeepInfraClient
                client = DeepInfraClient()
                
                scores = client.rerank_sync("query", ["doc1", "doc2", "doc3"])
                
                assert len(scores) == 3
                assert scores[0] == 0.95
                assert scores[1] == 0.80
    
    def test_rerank_request_format(self):
        """Test rerank sends correct request format for Qwen model"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            with patch('deepinfra_client.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = {"scores": [0.5]}
                mock_response.raise_for_status = MagicMock()
                
                mock_post = MagicMock(return_value=mock_response)
                mock_client.return_value.__enter__.return_value.post = mock_post
                
                from deepinfra_client import DeepInfraClient
                client = DeepInfraClient()
                client.rerank_sync("my query", ["document text"])
                
                # Verify the request format
                call_args = mock_post.call_args
                request_json = call_args.kwargs.get('json') or call_args[1].get('json')
                
                assert "queries" in request_json
                assert "documents" in request_json
                assert request_json["queries"] == ["my query"]
                assert request_json["documents"] == ["document text"]


class TestEmbeddingService:
    """Tests for EmbeddingService"""
    
    def test_uses_deepinfra_when_enabled(self):
        """Test service uses Deep Infra API when enabled"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            from embeddings import EmbeddingService
            service = EmbeddingService()
            
            assert service.use_deepinfra is True
    
    def test_uses_local_when_disabled(self):
        """Test service uses local model when Deep Infra disabled"""
        reset_modules()
        
        with patch.dict(os.environ, {"USE_DEEPINFRA": "false"}, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            from embeddings import EmbeddingService
            service = EmbeddingService()
            
            assert service.use_deepinfra is False
    
    def test_adds_instruction_prefix(self):
        """Test that instruction prefix is added correctly"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            with patch('deepinfra_client.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = {"embeddings": [[0.1] * 768]}
                mock_response.raise_for_status = MagicMock()
                
                mock_post = MagicMock(return_value=mock_response)
                mock_client.return_value.__enter__.return_value.post = mock_post
                
                from embeddings import EmbeddingService
                import deepinfra_client
                deepinfra_client._client = None
                
                service = EmbeddingService()
                
                # Test query instruction
                service.generate_embeddings(["test"], instruction="query")
                call_args = mock_post.call_args
                request_json = call_args.kwargs.get('json') or call_args[1].get('json')
                assert request_json["inputs"][0].startswith("query: ")
                
                # Test passage instruction
                service.generate_embeddings(["test"], instruction="passage")
                call_args = mock_post.call_args
                request_json = call_args.kwargs.get('json') or call_args[1].get('json')
                assert request_json["inputs"][0].startswith("passage: ")


class TestRerankService:
    """Tests for RerankService"""
    
    def test_rerank_sorts_by_score(self):
        """Test that rerank returns documents sorted by score"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            with patch('deepinfra_client.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = {"scores": [0.3, 0.9, 0.6]}
                mock_response.raise_for_status = MagicMock()
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                
                from rerank import RerankService
                import deepinfra_client
                deepinfra_client._client = None
                
                service = RerankService()
                
                docs = [
                    {"title": "Doc A", "description": "First"},
                    {"title": "Doc B", "description": "Second"},
                    {"title": "Doc C", "description": "Third"},
                ]
                
                results, scores = service.rerank("query", docs, top_n=3)
                
                # Should be sorted by score descending
                assert results[0]["title"] == "Doc B"  # score 0.9
                assert results[1]["title"] == "Doc C"  # score 0.6
                assert results[2]["title"] == "Doc A"  # score 0.3
                assert scores == [0.9, 0.6, 0.3]
    
    def test_rerank_respects_top_n(self):
        """Test that rerank returns only top_n results"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            with patch('deepinfra_client.httpx.Client') as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = {"scores": [0.3, 0.9, 0.6]}
                mock_response.raise_for_status = MagicMock()
                mock_client.return_value.__enter__.return_value.post.return_value = mock_response
                
                from rerank import RerankService
                import deepinfra_client
                deepinfra_client._client = None
                
                service = RerankService()
                
                docs = [
                    {"title": "Doc A"},
                    {"title": "Doc B"},
                    {"title": "Doc C"},
                ]
                
                results, scores = service.rerank("query", docs, top_n=2)
                
                assert len(results) == 2
                assert len(scores) == 2
    
    def test_rerank_empty_documents(self):
        """Test rerank handles empty document list"""
        reset_modules()
        
        with patch.dict(os.environ, {
            "USE_DEEPINFRA": "true",
            "DEEPINFRA_API_KEY": "test-key"
        }, clear=False):
            from config import get_settings
            get_settings.cache_clear()
            
            from rerank import RerankService
            service = RerankService()
            
            results, scores = service.rerank("query", [], top_n=5)
            
            assert results == []
            assert scores == []
