# Architecture Documentation

## Overview

Smart Clipboard Manager follows a clean architecture pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                    │
│  ┌──────────────┐    ┌──────────────┐                   │
│  │     CLI      │    │   REST API   │                   │
│  │  (main.py)   │    │  (server.py) │                   │
│  └──────────────┘    └──────────────┘                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Domain Layer                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐   │
│  │ Clipboard    │    │ ML Models    │    │ Storage  │   │
│  │ Monitor      │◄──►│ Classifier   │    │ Service  │   │
│  │              │    │ Searcher     │    │          │   │
│  └──────────────┘    └──────────────┘    └──────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐   │
│  │ pyperclip    │    │ scikit-learn │    │ SQLite   │   │
│  │ System APIs  │    │ transformers │    | SQLAlchemy│  │
│  └──────────────┘    └──────────────┘    └──────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Core Components

### Clipboard Monitor (`src/clipboard/monitor.py`)

- Runs as a background thread
- Polls system clipboard at configurable intervals
- Detects content type automatically (text, code, URL, command)
- Triggers callbacks when new content is captured
- Handles deduplication to avoid storing identical clips

### Storage Service (`src/clipboard/storage.py`)

- SQLite-based persistent storage using SQLAlchemy ORM
- Automatic deduplication via content hashing
- Full-text search support
- Metadata tracking (type, category, tags, access count)
- Thread-safe session management

### ML Classifier (`src/ml/classifier.py`)

- Rule-based classification for fast, accurate detection of common types
- TF-IDF + K-Means clustering for unsupervised categorization
- Configurable confidence thresholds
- Fallback to default category when uncertain

### Semantic Search (`src/ml/searcher.py`)

- Optional sentence-transformers integration for semantic search
- Fallback to word-overlap search when model unavailable
- Cosine similarity scoring
- Incremental index building

## Data Flow

1. **Capture**: Clipboard Monitor detects new content
2. **Classify**: ML Classifier determines content type/category
3. **Store**: Storage Service persists with metadata
4. **Index**: Semantic Search builds embedding (if enabled)
5. **Retrieve**: CLI/API queries return filtered/sorted results

## Configuration

All configuration is managed through `src/utils/config.py`:

- Environment variables (`CLIPBOARD_*`)
- `.env` file support
- Default values for all settings
- Pydantic validation

## Testing Strategy

- Unit tests for each component
- Integration tests for workflows
- Mock external dependencies where needed
- Test coverage target: 80%+

## Future Enhancements

1. **Cross-device Sync**: Encrypted sync via cloud storage
2. **Image Support**: OCR and image embedding search
3. **GUI**: Tauri/React desktop application
4. **Plugins**: Extensible plugin system for custom actions
5. **Hotkeys**: Global keyboard shortcuts for quick capture
