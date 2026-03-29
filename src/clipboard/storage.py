"""Clip storage and retrieval using SQLite."""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

from ..utils.config import get_config

Base = declarative_base()


@dataclass
class Clip:
    """Represents a clipboard clip."""
    id: Optional[int] = None
    content: str = ""
    clip_type: str = "text"
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    similarity_hash: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert clip to dictionary."""
        return {
            "id": self.id,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "full_content": self.content,
            "clip_type": self.clip_type,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "access_count": self.access_count,
        }


class ClipDatabase(Base):
    """SQLAlchemy model for clips."""
    
    __tablename__ = "clips"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    content_hash = Column(String(64), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    clip_type = Column(String(20), default="text")
    category = Column(String(50), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=func.now())
    access_count = Column(Integer, default=0)
    embedding = Column(Text, nullable=True)  # Base64 encoded embedding


class ClipStorage:
    """Handles storage and retrieval of clips."""
    
    def __init__(self):
        config = get_config()
        self.db_path = config.db_path
        
        # Initialize database
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(bind=self.engine)
        self.SessionLocal = SessionLocal
    
    def _content_hash(self, content: str) -> str:
        """Generate hash for content deduplication."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def add_clip(self, content: str, clip_type: str = "text") -> Clip:
        """Add a new clip to storage."""
        content_hash = self._content_hash(content)
        
        with self.SessionLocal() as session:
            # Check for duplicates
            existing = session.query(ClipDatabase).filter_by(
                content_hash=content_hash
            ).first()
            
            if existing:
                # Increment access count
                existing.access_count += 1
                session.commit()
                return Clip(
                    id=existing.id,
                    content=existing.content,
                    clip_type=existing.clip_type,
                    category=existing.category,
                    tags=self._parse_tags(existing.tags),
                    created_at=existing.created_at,
                    access_count=existing.access_count,
                )
            
            # Create new clip
            new_clip = ClipDatabase(
                content_hash=content_hash,
                content=content,
                clip_type=clip_type,
            )
            session.add(new_clip)
            session.commit()
            
            return Clip(
                id=new_clip.id,
                content=content,
                clip_type=clip_type,
            )
    
    def get_clip(self, clip_id: int) -> Optional[Clip]:
        """Retrieve a clip by ID."""
        with self.SessionLocal() as session:
            db_clip = session.query(ClipDatabase).filter_by(id=clip_id).first()
            
            if not db_clip:
                return None
            
            # Increment access count
            db_clip.access_count += 1
            session.commit()
            
            return Clip(
                id=db_clip.id,
                content=db_clip.content,
                clip_type=db_clip.clip_type,
                category=db_clip.category,
                tags=self._parse_tags(db_clip.tags),
                created_at=db_clip.created_at,
                access_count=db_clip.access_count,
            )
    
    def get_recent(self, limit: int = 10) -> List[Clip]:
        """Get most recent clips."""
        with self.SessionLocal() as session:
            clips = session.query(ClipDatabase)\
                .order_by(ClipDatabase.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                Clip(
                    id=c.id,
                    content=c.content,
                    clip_type=c.clip_type,
                    category=c.category,
                    tags=self._parse_tags(c.tags),
                    created_at=c.created_at,
                    access_count=c.access_count,
                )
                for c in clips
            ]
    
    def search(self, query: str, limit: int = 10) -> List[Clip]:
        """Search clips using full-text search."""
        with self.SessionLocal() as session:
            # Simple text search (will be enhanced with embeddings later)
            clips = session.query(ClipDatabase)\
                .filter(ClipDatabase.content.ilike(f"%{query}%"))\
                .order_by(ClipDatabase.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [
                Clip(
                    id=c.id,
                    content=c.content,
                    clip_type=c.clip_type,
                    category=c.category,
                    tags=self._parse_tags(c.tags),
                    created_at=c.created_at,
                    access_count=c.access_count,
                )
                for c in clips
            ]
    
    def update_category(self, clip_id: int, category: str) -> bool:
        """Update the category of a clip."""
        with self.SessionLocal() as session:
            clip = session.query(ClipDatabase).filter_by(id=clip_id).first()
            if not clip:
                return False
            
            clip.category = category
            session.commit()
            return True
    
    def add_tags(self, clip_id: int, tags: List[str]) -> bool:
        """Add tags to a clip."""
        with self.SessionLocal() as session:
            clip = session.query(ClipDatabase).filter_by(id=clip_id).first()
            if not clip:
                return False
            
            existing_tags = self._parse_tags(clip.tags)
            new_tags = list(set(existing_tags + tags))
            clip.tags = self._serialize_tags(new_tags)
            session.commit()
            return True
    
    def _parse_tags(self, tags_str: Optional[str]) -> List[str]:
        """Parse tags from JSON string."""
        if not tags_str:
            return []
        import json
        try:
            return json.loads(tags_str)
        except:
            return []
    
    def _serialize_tags(self, tags: List[str]) -> str:
        """Serialize tags to JSON string."""
        import json
        return json.dumps(tags)
    
    def get_stats(self) -> dict:
        """Get storage statistics."""
        with self.SessionLocal() as session:
            total = session.query(ClipDatabase).count()
            by_type = session.query(
                ClipDatabase.clip_type, 
                func.count(ClipDatabase.id)
            ).group_by(ClipDatabase.clip_type).all()
            
            return {
                "total_clips": total,
                "by_type": {t: c for t, c in by_type},
            }
