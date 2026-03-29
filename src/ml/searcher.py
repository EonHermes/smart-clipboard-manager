"""Semantic search using sentence embeddings."""

import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class SemanticSearch:
    """Semantic search for clipboard clips using embeddings."""
    
    def __init__(self):
        self.model = None
        self.embeddings: Dict[int, np.ndarray] = {}
        self._loaded = False
    
    def _load_model(self):
        """Load the sentence transformer model."""
        if self._loaded:
            return
        
        try:
            from sentence_transformers import SentenceTransformer
            from ..utils.config import get_config
            
            config = get_config()
            self.model = SentenceTransformer(config.model_name)
            self._loaded = True
        except ImportError:
            # Fallback to simple search if model not available
            self.model = None
            print("Note: Install sentence-transformers for semantic search")
    
    def encode(self, text: str) -> np.ndarray:
        """Encode text into embedding vector."""
        self._load_model()
        
        if self.model is None:
            # Fallback: simple hash-based encoding using built-in hash
            import hashlib
            hash_bytes = hashlib.md5(text.encode()).digest()
            return np.frombuffer(hash_bytes, dtype=np.uint8).astype(np.float32)
        
        return self.model.encode([text])[0]
    
    def add_clip(self, clip_id: int, content: str):
        """Add a clip's embedding for search."""
        embedding = self.encode(content)
        self.embeddings[clip_id] = embedding
    
    def remove_clip(self, clip_id: int):
        """Remove a clip from search index."""
        if clip_id in self.embeddings:
            del self.embeddings[clip_id]
    
    def search(self, query: str, clips: List[Dict], limit: int = 10) -> List[Tuple[Dict, float]]:
        """Search clips semantically.
        
        Args:
            query: Search query string
            clips: List of clip dictionaries with 'id' and 'content'
            limit: Maximum results to return
            
        Returns:
            List of (clip, similarity_score) tuples sorted by relevance
        """
        self._load_model()
        
        if not clips or self.model is None:
            # Fallback to simple text search
            return self._simple_search(query, clips, limit)
        
        # Encode query
        query_embedding = self.encode(query)
        
        results = []
        for clip in clips:
            clip_id = clip.get("id")
            
            # Get or compute embedding
            if clip_id not in self.embeddings:
                content = clip.get("content", "")
                self.add_clip(clip_id, content)
            
            embedding = self.embeddings[clip_id]
            
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            results.append((clip, float(similarity)))
        
        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _simple_search(self, query: str, clips: List[Dict], limit: int = 10) -> List[Tuple[Dict, float]]:
        """Fallback simple text-based search."""
        query_lower = query.lower()
        results = []
        
        for clip in clips:
            content = clip.get("content", "").lower()
            
            # Calculate simple similarity based on word overlap
            query_words = set(query_lower.split())
            content_words = set(content.split())
            
            if not query_words or not content_words:
                continue
            
            overlap = len(query_words & content_words)
            similarity = overlap / max(len(query_words), 1)
            
            # Boost for exact substring match
            if query_lower in content:
                similarity = min(1.0, similarity + 0.5)
            
            if similarity > 0:
                results.append((clip, float(similarity)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return float(dot_product / (norm_a * norm_b))
    
    def rebuild_index(self, clips: List[Dict]):
        """Rebuild the entire search index."""
        self.embeddings.clear()
        
        for clip in clips:
            clip_id = clip.get("id")
            content = clip.get("content", "")
            if clip_id and content:
                self.add_clip(clip_id, content)
