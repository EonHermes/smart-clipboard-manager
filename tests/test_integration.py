"""Integration tests for the full system."""

import pytest
import tempfile
from pathlib import Path
import json

from src.clipboard.storage import ClipStorage
from src.ml.classifier import ContentClassifier
from src.ml.searcher import SemanticSearch


class TestFullWorkflow:
    """Test complete workflows."""
    
    @pytest.fixture(autouse=True)
    def setup_storage(self):
        """Set up test storage with sample data for each test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            # Create a fresh storage instance per test
            from sqlalchemy import create_engine
            from src.clipboard.storage import Base, ClipStorage
            
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            
            storage = ClipStorage()
            storage.db_path = db_path
            storage.engine = engine
            from sqlalchemy.orm import sessionmaker
            storage.SessionLocal = sessionmaker(bind=engine)
            
            yield storage
    
    def test_add_and_retrieve(self, setup_storage):
        """Test adding a clip and retrieving it."""
        # Add clip
        clip = setup_storage.add_clip("def hello():\n    print('Hello')", "code")
        
        # Retrieve
        retrieved = setup_storage.get_clip(clip.id)
        
        assert retrieved is not None
        assert retrieved.content == clip.content
        assert retrieved.clip_type == "code"
    
    def test_classify_and_store(self, setup_storage):
        """Test classifying content before storing."""
        classifier = ContentClassifier()
        content = "https://github.com/EonHermes/smart-clipboard-manager"
        
        # Classify first
        classification = classifier.classify(content)
        
        # Store with detected type
        clip = setup_storage.add_clip(content, classification["category"])
        
        assert clip.clip_type == "url"
    
    def test_search_after_adding(self, setup_storage):
        """Test searching after adding multiple clips."""
        # Add various clips
        setup_storage.add_clip("Python function definition", "code")
        setup_storage.add_clip("https://example.com/api/docs", "url")
        setup_storage.add_clip("npm install express", "command")
        
        # Search for python
        results = setup_storage.search("python")
        
        assert len(results) >= 1
        assert any("python" in r.content.lower() for r in results)
    
    def test_full_search_workflow(self, setup_storage):
        """Test complete search workflow with ML."""
        # Add clips
        clips_data = [
            ("React component example", "code"),
            ("Vue.js tutorial link", "url"),
            ("Angular service pattern", "code"),
            ("Random note about meeting", "text"),
        ]
        
        for content, clip_type in clips_data:
            setup_storage.add_clip(content, clip_type)
        
        # Use semantic search
        searcher = SemanticSearch()
        all_clips = setup_storage.get_recent(limit=10)
        
        results = searcher.search("react component", [c.to_dict() for c in all_clips])
        
        # Should find React-related content
        assert len(results) > 0
    
    def test_export_import_workflow(self, setup_storage):
        """Test export and potential import workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use the fixture's storage which is already isolated
            
            # Add some clips
            setup_storage.add_clip("Clip one", "text")
            setup_storage.add_clip("Clip two", "code")
            
            # Export only these 2 clips (use limit=2)
            clips = setup_storage.get_recent(limit=2)
            export_data = {
                "clips": [c.to_dict() for c in clips],
            }
            
            export_path = Path(tmpdir) / "export.json"
            with open(export_path, 'w') as f:
                json.dump(export_data, f)
            
            # Verify export
            assert export_path.exists()
            
            with open(export_path) as f:
                imported = json.load(f)
            
            assert len(imported["clips"]) == 2


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture(autouse=True)
    def setup_storage(self):
        """Set up test storage for each test."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            
            from sqlalchemy import create_engine
            from src.clipboard.storage import Base, ClipStorage
            
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine)
            
            storage = ClipStorage()
            storage.db_path = db_path
            storage.engine = engine
            from sqlalchemy.orm import sessionmaker
            storage.SessionLocal = sessionmaker(bind=engine)
            
            yield storage
    
    def test_empty_content(self, setup_storage):
        """Test handling of empty content."""
        clip = setup_storage.add_clip("", "text")
        
        # Should still create a clip (empty is valid)
        assert clip.id is not None
    
    def test_very_long_content(self, setup_storage):
        """Test handling of very long content."""
        long_content = "Line\n" * 10000
        
        clip = setup_storage.add_clip(long_content, "text")
        
        assert clip.content == long_content
    
    def test_special_characters(self, setup_storage):
        """Test handling of special characters."""
        content = "Special chars: <>&\"'\\n\\t🎉"
        
        clip = setup_storage.add_clip(content, "text")
        
        assert clip.content == content
    
    def test_unicode_content(self, setup_storage):
        """Test handling of Unicode content."""
        content = "Unicode: 你好世界 🌍 مرحبا بالعالم"
        
        clip = setup_storage.add_clip(content, "text")
        
        assert clip.content == content
