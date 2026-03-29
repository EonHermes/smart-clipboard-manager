# Smart Clipboard Manager 📋

A intelligent clipboard manager that learns what you copy and suggests contextually relevant clips. Features AI-powered search, automatic categorization, and a beautiful interface.

## Features

- **Smart Capture**: Automatically captures clipboard content (text, images, code)
- **AI Categorization**: Uses ML to automatically categorize clips by type and context
- **Semantic Search**: Find clips using natural language queries
- **Contextual Suggestions**: Gets smarter about what you need based on your workflow
- **Privacy-First**: All processing happens locally on your machine
- **Keyboard Driven**: Fast, efficient workflow without leaving keyboard

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python -m src.main

# Or start the server for GUI integration
python -m src.server --host 0.0.0.0 --port 8080
```

## Architecture

```
smart-clipboard-manager/
├── src/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── server.py         # REST API server
│   ├── clipboard/        # Clipboard handling
│   │   ├── __init__.py
│   │   ├── monitor.py    # Background monitoring
│   │   └── storage.py    # Local storage management
│   ├── ml/               # Machine learning components
│   │   ├── __init__.py
│   │   ├── classifier.py # Content categorization
│   │   └── searcher.py   # Semantic search
│   └── utils/            # Utilities
│       ├── __init__.py
│       └── config.py     # Configuration management
├── tests/
│   ├── test_clipboard.py
│   ├── test_ml.py
│   └── test_integration.py
├── data/                 # Local storage for clips
├── docs/                 # Documentation
└── requirements.txt
```

## Usage Examples

### CLI Commands

```bash
# List recent clips
python -m src.main list --limit 10

# Search for clips
python -m src.main search "react component example"

# Categorize a clip manually
python -m src.main categorize --id 123 --category code

# Export clips
python -m src.main export --format json --output backups/
```

### API Endpoints

```bash
# Get recent clips
curl http://localhost:8080/api/clips?limit=10

# Search clips
curl "http://localhost:8080/api/search?q=python%20function"

# Add clip manually
curl -X POST http://localhost:8080/api/clips \
  -H "Content-Type: application/json" \
  -d '{"text": "your content", "type": "text"}'
```

## Tech Stack

- **Backend**: Python 3.10+ with FastAPI
- **ML**: scikit-learn, sentence-transformers for embeddings
- **Storage**: SQLite with full-text search
- **Clipboard**: `pyperclip` + system-specific backends
- **Testing**: pytest with comprehensive coverage

## Development

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov=src

# Run with hot-reload
uvicorn src.server:app --reload
```

## Roadmap

- [x] Core clipboard monitoring
- [x] Basic categorization
- [x] Semantic search
- [ ] Image support
- [ ] Cross-device sync
- [ ] React/Tauri GUI
- [ ] Plugin system

## License

MIT - See LICENSE for details.
