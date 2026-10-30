# Document Compressor

Production-oriented Image and PDF compression platform built with FastAPI, independent compression engines, Celery background tasks, PostgreSQL, and Redis.

## Architecture

Modular monolith with clean separation of concerns:
- **Core Compression Engines (`app/engines/`)**: Completely independent of FastAPI, PostgreSQL, and Celery for portability and reuse.
  - Image engine: Presets, target-size optimization, transparency handling, EXIF correction, metadata preservation.
  - PDF engine: Lossless optimization, stream compression, image downsampling/re-encoding, structure cleanup.
- **API (`app/api/`)**: FastAPI REST endpoints for single and batch compression jobs.
- **Database & Jobs (`app/database/`, `app/services/`)**: PostgreSQL with SQLAlchemy 2.x & Alembic.
- **Background Workers (`app/workers/`)**: Celery + Redis with task orchestration and failure isolation.

## Setup

Requires Python 3.15+ and `uv`.

```bash
# Sync dependencies
uv sync

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run formatting check
uv run ruff format --check .
```
