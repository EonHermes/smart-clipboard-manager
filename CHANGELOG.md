# Changelog

All notable changes to Smart Clipboard Manager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release with core functionality
- CLI interface with list, search, capture, monitor commands
- REST API server with FastAPI
- SQLite storage with SQLAlchemy ORM
- Rule-based content classification (URL, code, email, command detection)
- TF-IDF + K-Means clustering for unsupervised categorization
- Semantic search with sentence-transformers (optional)
- Fallback word-overlap search when ML model unavailable
- Comprehensive test suite
- Full documentation

### TODO
- Image clipboard support with OCR
- Cross-device synchronization
- React/Tauri GUI application
- Plugin system for custom actions
- Global hotkey support
- Export/import functionality improvements
- Webhook integrations

## [0.1.0] - 2026-03-29

### Added
- First public release
- All features listed above
