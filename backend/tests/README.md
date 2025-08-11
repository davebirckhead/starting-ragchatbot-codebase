# Backend Tests

This directory contains the test suite for the RAG system backend.

## Test Structure

### Test Files
- `test_api_endpoints.py` - API endpoint tests for FastAPI routes
- `test_static_files.py` - Static file serving and frontend integration tests
- `conftest.py` - Shared test fixtures and configuration

### Test Categories

#### API Tests (`@pytest.mark.api`)
- `/api/query` endpoint testing
- `/api/courses` endpoint testing  
- Root endpoint testing
- Error handling and validation
- CORS and headers testing

#### Integration Tests (`@pytest.mark.integration`)
- Multi-endpoint workflows
- Concurrent request handling
- Full application integration scenarios

#### Unit Tests (`@pytest.mark.unit`)
- Component-level testing
- Configuration testing
- Utility function testing

## Running Tests

### Install Test Dependencies
```bash
uv sync --extra test
```

### Run All Tests
```bash
cd backend
uv run pytest
```

### Run Specific Test Categories
```bash
# API tests only
uv run pytest -m api

# Integration tests only  
uv run pytest -m integration

# Unit tests only
uv run pytest -m unit
```

### Run Specific Test Files
```bash
# API endpoint tests
uv run pytest tests/test_api_endpoints.py

# Static file tests
uv run pytest tests/test_static_files.py
```

### Run with Verbose Output
```bash
uv run pytest -v
```

### Run with Coverage
```bash
uv run pytest --cov=. --cov-report=html
```

## Test Configuration

Test configuration is defined in `pyproject.toml`:
- Test discovery patterns
- Marker definitions
- Async test handling
- Output formatting

## Fixtures

The `conftest.py` file provides shared fixtures:

- `temp_dir` - Temporary directory for test files
- `mock_config` - Test configuration
- `sample_courses` - Sample course data
- `sample_chunks` - Sample course chunks
- `mock_rag_system` - Mocked RAG system
- `test_app` - Test FastAPI application
- `client` - Test client for API requests
- `sample_query_data` - Sample query request data

## Mocking Strategy

Tests use comprehensive mocking to avoid external dependencies:
- ChromaDB operations are mocked
- Anthropic API calls are mocked
- File system operations use temporary directories
- Static file mounting issues are handled with test-specific apps

## Key Testing Patterns

### API Testing
- Request/response validation
- Error handling verification
- Content-type and header checking
- Concurrent request testing

### Static File Testing  
- Alternative serving strategies
- Cache header configuration
- MIME type handling
- Integration scenarios

### Mock Integration
- RAG system component mocking
- External API mocking
- Database operation mocking
- Session management mocking