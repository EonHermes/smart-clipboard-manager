#!/usr/bin/env python3
"""Smart Clipboard Manager - REST API Server."""

from contextlib import asynccontextmanager
from typing import Optional
import asyncio

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .utils.config import get_config
from .clipboard.storage import ClipStorage, Clip
from .clipboard.monitor import ClipboardMonitor
from .ml.classifier import ContentClassifier
from .ml.searcher import SemanticSearch


# Pydantic models for API
class ClipCreate(BaseModel):
    """Request model for creating a clip."""
    text: str
    clip_type: Optional[str] = "text"


class ClipResponse(BaseModel):
    """Response model for a clip."""
    id: int
    content: str
    clip_type: str
    category: Optional[str]
    tags: list[str]
    created_at: str
    access_count: int


class SearchResponse(BaseModel):
    """Response model for search results."""
    query: str
    results: list[ClipResponse]
    total: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    config = get_config()
    storage = ClipStorage()
    
    # Start clipboard monitor in background
    monitor = ClipboardMonitor(storage)
    app.state.monitor = monitor
    monitor.start()
    
    # Initialize ML components
    app.state.classifier = ContentClassifier()
    app.state.searcher = SemanticSearch()
    
    yield
    
    # Shutdown
    if hasattr(app.state, 'monitor'):
        app.state.monitor.stop()


# Create FastAPI app
app = FastAPI(
    title="Smart Clipboard Manager API",
    description="AI-powered clipboard management with semantic search and automatic categorization.",
    version="0.1.0",
    lifespan=lifespan,
)


def clip_to_response(clip: Clip) -> ClipResponse:
    """Convert Clip to API response model."""
    return ClipResponse(
        id=clip.id or 0,
        content=clip.content[:500] + "..." if len(clip.content) > 500 else clip.content,
        clip_type=clip.clip_type,
        category=clip.category,
        tags=clip.tags,
        created_at=clip.created_at.isoformat(),
        access_count=clip.access_count,
    )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    config = get_config()
    return {
        "name": config.app_name,
        "version": config.app_version,
        "status": "running",
        "endpoints": ["/api/clips", "/api/search", "/api/stats", "/api/capture"],
    }


@app.get("/api/clips", response_model=list[ClipResponse])
async def list_clips(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """List recent clips."""
    storage = ClipStorage()
    all_clips = storage.get_recent(limit=limit + offset)
    clips = all_clips[offset:]
    return [clip_to_response(clip) for clip in clips]


@app.get("/api/clips/{clip_id}", response_model=ClipResponse)
async def get_clip(clip_id: int):
    """Get a specific clip by ID."""
    storage = ClipStorage()
    clip = storage.get_clip(clip_id)
    
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return clip_to_response(clip)


@app.post("/api/clips", response_model=ClipResponse)
async def create_clip(clip_data: ClipCreate):
    """Manually add a clip."""
    storage = ClipStorage()
    classifier = ContentClassifier()
    
    # Create clip
    clip = storage.add_clip(clip_data.text, clip_data.clip_type or "text")
    
    # Auto-categorize if not specified
    if not clip_data.clip_type:
        classification = classifier.classify(clip_data.text)
        storage.update_category(clip.id, classification["category"])
        clip.category = classification["category"]
    
    return clip_to_response(clip)


@app.delete("/api/clips/{clip_id}")
async def delete_clip(clip_id: int):
    """Delete a clip (placeholder for future implementation)."""
    raise HTTPException(status_code=501, detail="Delete not yet implemented")


@app.get("/api/search", response_model=SearchResponse)
async def search_clips(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50),
):
    """Search clips using semantic search."""
    storage = ClipStorage()
    
    # Get all clips for search
    all_clips = storage.get_recent(limit=1000)
    
    # Use semantic search if available
    searcher = SemanticSearch()
    results = searcher.search(q, [c.to_dict() for c in all_clips], limit=limit)
    
    # Convert to response format
    clip_responses = []
    for clip_dict, score in results:
        clip = Clip(
            id=clip_dict["id"],
            content=clip_dict.get("full_content", clip_dict["content"]),
            clip_type=clip_dict["clip_type"],
            category=clip_dict.get("category"),
            tags=clip_dict.get("tags", []),
            created_at=clip_dict["created_at"],
            access_count=clip_dict.get("access_count", 0),
        )
        clip_responses.append(clip_to_response(clip))
    
    return SearchResponse(
        query=q,
        results=clip_responses,
        total=len(results),
    )


@app.post("/api/capture", response_model=ClipResponse)
async def capture_clipboard():
    """Manually trigger clipboard capture."""
    storage = ClipStorage()
    monitor = ClipboardMonitor(storage)
    
    result = monitor.capture_now()
    
    if not result:
        raise HTTPException(status_code=400, detail="No content in clipboard")
    
    return clip_to_response(
        Clip(
            id=result["id"],
            content=result.get("full_content", result["content"]),
            clip_type=result["clip_type"],
            category=result.get("category"),
            tags=result.get("tags", []),
            created_at=result.get("created_at", ""),
            access_count=result.get("access_count", 0),
        )
    )


@app.post("/api/clips/{clip_id}/categorize")
async def categorize_clip(clip_id: int, category: str):
    """Manually categorize a clip."""
    storage = ClipStorage()
    
    if not storage.update_category(clip_id, category):
        raise HTTPException(status_code=404, detail="Clip not found")
    
    return {"message": f"Clip {clip_id} categorized as '{category}'"}


@app.get("/api/stats")
async def get_stats():
    """Get clipboard statistics."""
    storage = ClipStorage()
    stats = storage.get_stats()
    
    return {
        "total_clips": stats["total_clips"],
        "by_type": stats["by_type"],
        "data_dir": str(get_config().data_dir),
    }


@app.post("/api/classify")
async def classify_content(text: str):
    """Classify content without storing."""
    classifier = ContentClassifier()
    result = classifier.classify(text)
    return result


if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(app, host=config.host, port=config.port)
