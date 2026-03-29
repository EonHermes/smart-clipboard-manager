#!/usr/bin/env python3
"""Example usage of Smart Clipboard Manager."""

import sys
sys.path.insert(0, '..')

from src.clipboard.storage import ClipStorage
from src.ml.classifier import ContentClassifier
from src.ml.searcher import SemanticSearch


def example_basic_usage():
    """Basic clipboard storage and retrieval."""
    print("=== Basic Usage Example ===\n")
    
    # Create storage
    storage = ClipStorage()
    
    # Add some clips
    clips_to_add = [
        ("def hello_world():\n    print('Hello, World!')", "code"),
        ("https://github.com/EonHermes/smart-clipboard-manager", "url"),
        ("npm install fastapi uvicorn pyperclip", "command"),
        ("Meeting notes: Discuss project roadmap at 3pm", "text"),
    ]
    
    for content, clip_type in clips_to_add:
        clip = storage.add_clip(content, clip_type)
        print(f"✓ Added clip #{clip.id} ({clip_type})")
    
    # List recent clips
    print("\nRecent clips:")
    for clip in storage.get_recent(limit=5):
        preview = clip.content[:50] + "..." if len(clip.content) > 50 else clip.content
        print(f"  #{clip.id} [{clip.clip_type}] {preview}")


def example_classification():
    """Automatic content classification."""
    print("\n=== Classification Example ===\n")
    
    classifier = ContentClassifier()
    
    test_contents = [
        "https://example.com/api/docs",
        "def calculate_sum(a, b):\n    return a + b",
        "git push origin main",
        "Contact us at support@example.com",
        "Just some regular text content",
    ]
    
    for content in test_contents:
        result = classifier.classify(content)
        print(f"Content: {content[:40]}...")
        print(f"  → Category: {result['category']} (confidence: {result['confidence']:.2f})")
        print()


def example_search():
    """Semantic search examples."""
    print("=== Search Example ===\n")
    
    storage = ClipStorage()
    searcher = SemanticSearch()
    
    # Get all clips
    clips = storage.get_recent(limit=100)
    
    if not clips:
        print("No clips found. Run example_basic_usage first.")
        return
    
    # Search for different queries
    queries = ["python function", "npm package", "github repo"]
    
    for query in queries:
        print(f"Searching for: '{query}'")
        results = searcher.search(query, [c.to_dict() for c in clips], limit=3)
        
        for clip, score in results:
            preview = clip["content"][:40] + "..." if len(clip["content"]) > 40 else clip["content"]
            print(f"  Score {score:.3f}: {preview}")
        print()


def example_api_usage():
    """Example using the REST API."""
    print("=== API Usage Example ===\n")
    
    import httpx
    
    base_url = "http://127.0.0.1:8080"
    
    # List clips
    response = httpx.get(f"{base_url}/api/clips?limit=5")
    if response.status_code == 200:
        clips = response.json()
        print(f"Found {len(clips)} clips via API")
    
    # Search
    response = httpx.get(f"{base_url}/api/search?q=python&limit=3")
    if response.status_code == 200:
        results = response.json()
        print(f"Search returned {results['total']} results")


if __name__ == "__main__":
    example_basic_usage()
    example_classification()
    example_search()
    
    # Uncomment to test API (requires server running)
    # example_api_usage()
