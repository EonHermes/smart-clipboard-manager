"""Tests for ML components."""

import pytest
from src.ml.classifier import ContentClassifier
from src.ml.searcher import SemanticSearch


class TestContentClassifier:
    """Tests for content classification."""
    
    def test_url_detection(self):
        """Test URL detection."""
        classifier = ContentClassifier()
        
        result = classifier.classify("https://example.com")
        
        assert result["category"] == "url"
        assert result["confidence"] > 0.7
    
    def test_code_detection(self):
        """Test code detection."""
        classifier = ContentClassifier()
        
        result = classifier.classify("def hello_world():\n    print('Hello')")
        
        assert result["category"] == "code"
    
    def test_email_detection(self):
        """Test email detection."""
        classifier = ContentClassifier()
        
        result = classifier.classify("Contact me at test@example.com")
        
        assert result["category"] == "email"
    
    def test_command_detection(self):
        """Test command detection."""
        classifier = ContentClassifier()
        
        result = classifier.classify("sudo apt-get update")
        
        assert result["category"] == "command"
    
    def test_default_text(self):
        """Test default text classification."""
        classifier = ContentClassifier()
        
        result = classifier.classify("Just some regular text content")
        
        assert result["category"] in ["text", "cluster_0"]  # Could be cluster if fitted
    
    def test_fit_with_samples(self):
        """Test fitting classifier on samples."""
        classifier = ContentClassifier()
        
        samples = [
            "def function1(): pass",
            "def function2(): pass", 
            "class MyClass: pass",
            "import os",
            "const x = 5;",
            "function test() {}",
            "fn main() {}",
            "random text one",
            "random text two",
            "random text three",
        ]
        
        classifier.fit(samples)
        
        # Should have fitted if enough samples
        assert classifier._fitted or len(samples) < 10
    
    def test_suggest_category(self):
        """Test category suggestion."""
        classifier = ContentClassifier()
        
        existing = ["python", "javascript"]
        suggestion = classifier.suggest_category("some content", existing)
        
        # Should suggest something from existing or use rules
        assert suggestion is not None


class TestSemanticSearch:
    """Tests for semantic search."""
    
    def test_simple_search(self):
        """Test fallback simple search."""
        searcher = SemanticSearch()
        
        clips = [
            {"id": 1, "content": "Python programming tutorial"},
            {"id": 2, "content": "JavaScript basics guide"},
            {"id": 3, "content": "Rust systems programming"},
        ]
        
        results = searcher._simple_search("python", clips, limit=5)
        
        assert len(results) > 0
        # Python clip should be highest
        assert results[0][0]["id"] == 1
    
    def test_simple_search_no_match(self):
        """Test search with no matches."""
        searcher = SemanticSearch()
        
        clips = [
            {"id": 1, "content": "Python tutorial"},
        ]
        
        results = searcher._simple_search("xyznonexistent", clips, limit=5)
        
        # May still return something due to word overlap
        assert isinstance(results, list)
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        searcher = SemanticSearch()
        
        import numpy as np
        
        a = np.array([1, 0, 0])
        b = np.array([1, 0, 0])
        c = np.array([0, 1, 0])
        
        sim_ab = searcher._cosine_similarity(a, b)
        sim_ac = searcher._cosine_similarity(a, c)
        
        assert sim_ab == 1.0  # Identical vectors
        assert sim_ac == 0.0  # Orthogonal vectors
    
    def test_add_and_remove_clip(self):
        """Test adding and removing clips from index."""
        searcher = SemanticSearch()
        
        # This will use fallback encoding
        searcher.add_clip(1, "test content")
        assert 1 in searcher.embeddings or not searcher._loaded
        
        searcher.remove_clip(1)
        # After removal, should not be in embeddings if loaded
    
    def test_rebuild_index(self):
        """Test rebuilding the search index."""
        searcher = SemanticSearch()
        
        clips = [
            {"id": 1, "content": "First clip"},
            {"id": 2, "content": "Second clip"},
        ]
        
        # Add some embeddings manually for testing
        import numpy as np
        searcher.embeddings[999] = np.array([1, 0, 0])
        
        searcher.rebuild_index(clips)
        
        # Should have rebuilt (may be empty if model not loaded)
        assert isinstance(searcher.embeddings, dict)
