"""Tests for clipboard storage and monitoring."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from src.clipboard.storage import ClipStorage, Clip
from src.clipboard.monitor import ClipboardMonitor


@pytest.fixture
def temp_storage():
    """Create a temporary storage instance for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        storage = ClipStorage()
        # Override db path
        storage.db_path = db_path
        storage.engine = f"sqlite:///{db_path}"
        from sqlalchemy import create_engine
        from src.clipboard.storage import Base
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)
        storage.engine = engine
        from sqlalchemy.orm import sessionmaker
        storage.SessionLocal = sessionmaker(bind=engine)
        yield storage


class TestClipStorage:
    """Tests for ClipStorage class."""
    
    def test_add_clip(self, temp_storage):
        """Test adding a new clip."""
        clip = temp_storage.add_clip("Hello, World!", "text")
        
        assert clip.id is not None
        assert clip.content == "Hello, World!"
        assert clip.clip_type == "text"
    
    def test_add_duplicate_clip(self, temp_storage):
        """Test that duplicate clips are not added."""
        clip1 = temp_storage.add_clip("Duplicate content", "text")
        clip2 = temp_storage.add_clip("Duplicate content", "text")
        
        assert clip1.id == clip2.id
    
    def test_get_recent(self, temp_storage):
        """Test retrieving recent clips."""
        # Add multiple clips
        for i in range(5):
            temp_storage.add_clip(f"Clip {i}", "text")
        
        recent = temp_storage.get_recent(limit=3)
        
        assert len(recent) == 3
        assert all(isinstance(c, Clip) for c in recent)
    
    def test_search(self, temp_storage):
        """Test searching clips."""
        temp_storage.add_clip("Python function example", "code")
        temp_storage.add_clip("JavaScript code snippet", "code")
        temp_storage.add_clip("Random text content", "text")
        
        results = temp_storage.search("python")
        
        assert len(results) >= 1
        assert any("python" in c.content.lower() for c in results)
    
    def test_update_category(self, temp_storage):
        """Test updating clip category."""
        clip = temp_storage.add_clip("Some code", "code")
        
        result = temp_storage.update_category(clip.id, "python")
        
        assert result is True
        updated = temp_storage.get_clip(clip.id)
        assert updated.category == "python"
    
    def test_add_tags(self, temp_storage):
        """Test adding tags to a clip."""
        clip = temp_storage.add_clip("Code snippet", "code")
        
        result = temp_storage.add_tags(clip.id, ["python", "function"])
        
        assert result is True
        updated = temp_storage.get_clip(clip.id)
        assert "python" in updated.tags
        assert "function" in updated.tags
    
    def test_get_stats(self, temp_storage):
        """Test getting storage statistics."""
        temp_storage.add_clip("Text content", "text")
        temp_storage.add_clip("Code content", "code")
        temp_storage.add_clip("Another text", "text")
        
        stats = temp_storage.get_stats()
        
        assert stats["total_clips"] == 3
        assert stats["by_type"]["text"] == 2
        assert stats["by_type"]["code"] == 1
    
    def test_large_content(self, temp_storage):
        """Test handling of large content."""
        large_content = "x" * 100000
        
        clip = temp_storage.add_clip(large_content, "text")
        
        assert clip.content == large_content


class TestClip:
    """Tests for Clip dataclass."""
    
    def test_to_dict(self):
        """Test converting clip to dictionary."""
        clip = Clip(
            id=1,
            content="Test content",
            clip_type="text",
            category="general",
            tags=["test"],
            access_count=5,
        )
        
        result = clip.to_dict()
        
        assert result["id"] == 1
        assert result["clip_type"] == "text"
        assert result["category"] == "general"
        assert result["tags"] == ["test"]
    
    def test_to_dict_long_content(self):
        """Test that long content is truncated in preview."""
        clip = Clip(
            id=1,
            content="x" * 200,
            clip_type="text",
        )
        
        result = clip.to_dict()
        
        assert len(result["content"]) < 200
        assert "..." in result["content"]
