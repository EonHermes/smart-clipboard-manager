"""Configuration management for Smart Clipboard Manager."""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Application configuration."""

    # Application settings
    app_name: str = "Smart Clipboard Manager"
    app_version: str = "0.1.0"
    
    # Data storage
    data_dir: Path = Path.home() / ".smart-clipboard"
    db_path: Optional[Path] = None
    
    # Clipboard monitoring
    monitor_interval_ms: int = 500
    max_clip_size_bytes: int = 1_000_000  # 1MB
    supported_types: list[str] = ["text", "code", "url", "image"]
    
    # ML settings
    model_name: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.75
    
    # Server settings
    host: str = "127.0.0.1"
    port: int = 8080
    
    class Config:
        env_prefix = "CLIPBOARD_"
        env_file = ".env"


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create the global config instance."""
    global _config
    if _config is None:
        _config = Config()
        # Ensure data directory exists
        _config.data_dir.mkdir(parents=True, exist_ok=True)
        if _config.db_path is None:
            _config.db_path = _config.data_dir / "clips.db"
    return _config
