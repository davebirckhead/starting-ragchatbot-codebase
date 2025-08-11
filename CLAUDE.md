# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
- **Quick start**: `./run.sh` - Starts the entire application (ensure executable with `chmod +x run.sh`)
- **Manual start**: `cd backend && uv run uvicorn app:app --reload --port 8000`
- **Install dependencies**: `uv sync` (uses uv package manager)
- **Install dev dependencies**: `uv sync --extra dev` (includes Black, isort, flake8, mypy)

### Code Quality Tools
- **Format code**: `./scripts/format.sh` - Runs Black and isort
- **Lint code**: `./scripts/lint.sh` - Runs flake8 and mypy
- **All quality checks**: `./scripts/quality.sh` - Runs formatting and linting
- **Manual commands**:
  - `uv run black backend/ main.py` - Format with Black
  - `uv run isort backend/ main.py` - Sort imports
  - `uv run flake8 backend/ main.py` - Lint with flake8
  - `uv run mypy backend/ main.py` - Type check with mypy

### Environment Setup
- Create `.env` file in root with: `ANTHROPIC_API_KEY=your_key_here`
- Python 3.13+ required
- Uses `uv` as package manager (not pip)

### Application URLs
- Web Interface: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`

## Architecture Overview

### Core Components
This is a RAG (Retrieval-Augmented Generation) system with the following architecture:

**Backend (`/backend/`):**
- `app.py` - FastAPI application with CORS middleware, serves frontend static files and API endpoints
- `rag_system.py` - Main orchestrator coordinating all components
- `vector_store.py` - ChromaDB wrapper for embeddings and semantic search
- `ai_generator.py` - Anthropic Claude API integration with tool-based search
- `document_processor.py` - Document chunking and processing pipeline
- `session_manager.py` - Conversation history management
- `search_tools.py` - Tool manager and course search functionality
- `models.py` - Data classes for Course, Lesson, CourseChunk
- `config.py` - Configuration management with environment variables

**Frontend (`/frontend/`):**
- Static HTML/JS/CSS files served by FastAPI
- Single-page application for querying course materials

### Key Design Patterns

**Tool-Based RAG System:**
- AI uses search tools instead of direct vector queries
- `ToolManager` registers and manages search capabilities
- `CourseSearchTool` performs semantic search via ChromaDB
- Single search per query with source tracking

**Document Processing Pipeline:**
- Courses parsed from `/docs/` folder (PDF, DOCX, TXT)
- Content chunked with 800 character size, 100 character overlap
- Both metadata and content stored in ChromaDB collections
- Duplicate course detection by title

**Session Management:**
- Conversation history limited to 2 exchanges
- Session IDs for multi-turn conversations
- History passed to AI for context

### Configuration
- All settings centralized in `config.py` using dataclass
- ChromaDB path: `./chroma_db`
- Embedding model: `all-MiniLM-L6-v2`
- Claude model: `claude-sonnet-4-20250514`

### API Endpoints
- `POST /api/query` - Main query processing with RAG
- `GET /api/courses` - Course statistics and metadata
- Static file serving from `/frontend/`

The system automatically loads documents from `/docs/` on startup and supports incremental document addition without reprocessing existing courses.
- always use uv to run the server do not use pip directly
- make sure to use uv to manage all dependencies3