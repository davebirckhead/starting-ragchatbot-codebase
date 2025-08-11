import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
import os
import sys

# Add backend directory to Python path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import Config
from rag_system import RAGSystem
from models import Course, CourseChunk


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock configuration for testing"""
    config = Config(
        anthropic_api_key="test_api_key",
        chroma_db_path=f"{temp_dir}/test_chroma",
        embedding_model="all-MiniLM-L6-v2",
        claude_model="claude-sonnet-4-20250514",
        chunk_size=800,
        chunk_overlap=100,
        max_search_results=5,
        session_history_limit=2
    )
    return config


@pytest.fixture
def sample_courses():
    """Sample course data for testing"""
    return [
        Course(
            title="Test Course 1",
            filename="course1.txt",
            content="This is content for test course 1. It covers basic concepts."
        ),
        Course(
            title="Test Course 2", 
            filename="course2.txt",
            content="This is content for test course 2. It covers advanced topics."
        )
    ]


@pytest.fixture
def sample_chunks():
    """Sample course chunks for testing"""
    return [
        CourseChunk(
            course_title="Test Course 1",
            lesson_title="Lesson 1",
            content="This is content for test course 1.",
            chunk_id="chunk_1",
            metadata={"filename": "course1.txt"}
        ),
        CourseChunk(
            course_title="Test Course 2",
            lesson_title="Lesson 1", 
            content="This is content for test course 2.",
            chunk_id="chunk_2",
            metadata={"filename": "course2.txt"}
        )
    ]


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing"""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response from Claude")]
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def mock_vector_store(sample_chunks):
    """Mock vector store for testing"""
    mock_store = Mock()
    mock_store.search_courses.return_value = sample_chunks
    mock_store.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    }
    return mock_store


@pytest.fixture
def mock_rag_system(mock_config, mock_vector_store):
    """Mock RAG system for testing"""
    with patch('rag_system.VectorStore') as mock_vs_class, \
         patch('rag_system.AIGenerator') as mock_ai_class, \
         patch('rag_system.SessionManager') as mock_sm_class:
        
        mock_vs_class.return_value = mock_vector_store
        mock_ai_class.return_value = Mock()
        mock_sm_class.return_value = Mock()
        
        rag_system = RAGSystem(mock_config)
        rag_system.query = Mock(return_value=("Test answer", ["Test Course 1"]))
        rag_system.get_course_analytics = Mock(return_value={
            "total_courses": 2,
            "course_titles": ["Test Course 1", "Test Course 2"]
        })
        rag_system.add_course_folder = Mock(return_value=(2, 4))
        
        yield rag_system


@pytest.fixture
def test_app():
    """Create a test FastAPI app without static file mounting"""
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    from typing import List, Optional
    
    # Create test app without problematic static file mounting
    app = FastAPI(title="Test RAG System")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Pydantic models
    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]
    
    # Mock RAG system for the app
    mock_rag = Mock()
    mock_rag.query.return_value = ("Test response", ["Test Course 1"])
    mock_rag.get_course_analytics.return_value = {
        "total_courses": 2,
        "course_titles": ["Test Course 1", "Test Course 2"]
    }
    mock_rag.session_manager.create_session.return_value = "test_session_123"
    
    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag.session_manager.create_session()
            
            answer, sources = mock_rag.query(request.query, session_id)
            
            return QueryResponse(
                answer=answer,
                sources=sources,
                session_id=session_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/")
    async def root():
        return {"message": "RAG System API"}
    
    return app


@pytest.fixture
def client(test_app):
    """Create a test client for the FastAPI app"""
    return TestClient(test_app)


@pytest.fixture
def sample_query_data():
    """Sample query request data"""
    return {
        "valid_query": {
            "query": "What is the main topic of test course 1?",
            "session_id": "test_session_123"
        },
        "query_without_session": {
            "query": "Explain the concepts in the courses"
        },
        "empty_query": {
            "query": ""
        }
    }


@pytest.fixture 
def mock_docs_folder(temp_dir):
    """Create a mock docs folder with sample files"""
    docs_dir = Path(temp_dir) / "docs"
    docs_dir.mkdir()
    
    (docs_dir / "course1.txt").write_text("Sample content for course 1")
    (docs_dir / "course2.txt").write_text("Sample content for course 2")
    
    return str(docs_dir)