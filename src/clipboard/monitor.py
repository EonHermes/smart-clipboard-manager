"""Clipboard monitoring and capture."""

import time
import threading
from typing import Callable, Optional
import pyperclip

from .storage import ClipStorage


class ClipboardMonitor:
    """Monitors system clipboard for changes and captures content."""
    
    def __init__(self, storage: ClipStorage):
        self.storage = storage
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content: Optional[str] = None
        self._callbacks: list[Callable[[str, str], None]] = []
    
    def add_callback(self, callback: Callable[[str, str], None]):
        """Add a callback for when new content is captured.
        
        Args:
            callback: Function that receives (content, clip_type)
        """
        self._callbacks.append(callback)
    
    def _detect_type(self, content: str) -> str:
        """Detect the type of clipboard content."""
        # Check for URLs
        if content.startswith(("http://", "https://")):
            return "url"
        
        # Check for code patterns
        code_indicators = [
            "def ", "function ", "class ", "import ", "const ", 
            "let ", "var ", "fn ", "->", "{", "}", "<script"
        ]
        if any(indicator in content for indicator in code_indicators):
            return "code"
        
        # Check for very short content (likely commands/short text)
        if len(content.strip()) < 50:
            return "text"
        
        # Default to text
        return "text"
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        from ..utils.config import get_config
        config = get_config()
        
        while self._running:
            try:
                current_content = pyperclip.paste()
                
                # Skip if empty or same as last
                if not current_content or current_content == self._last_content:
                    time.sleep(config.monitor_interval_ms / 1000)
                    continue
                
                # Skip if too large
                if len(current_content) > config.max_clip_size_bytes:
                    time.sleep(config.monitor_interval_ms / 1000)
                    continue
                
                # Detect type and store
                clip_type = self._detect_type(current_content)
                clip = self.storage.add_clip(current_content, clip_type)
                
                # Update last content
                self._last_content = current_content
                
                # Notify callbacks
                for callback in self._callbacks:
                    try:
                        callback(current_content, clip_type)
                    except Exception as e:
                        print(f"Callback error: {e}")
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(config.monitor_interval_ms / 1000)
    
    def start(self):
        """Start monitoring the clipboard."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("Clipboard monitor started")
    
    def stop(self):
        """Stop monitoring the clipboard."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        print("Clipboard monitor stopped")
    
    def capture_now(self) -> Optional[dict]:
        """Manually capture current clipboard content."""
        try:
            content = pyperclip.paste()
            if not content:
                return None
            
            clip_type = self._detect_type(content)
            clip = self.storage.add_clip(content, clip_type)
            
            return clip.to_dict()
        except Exception as e:
            print(f"Capture error: {e}")
            return None
