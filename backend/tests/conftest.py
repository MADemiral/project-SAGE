"""
Pytest configuration and fixtures for backend tests
"""
import pytest
import os
import sys
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Mock external dependencies that might not be installed
sys.modules['groq'] = MagicMock()
sys.modules['langdetect'] = MagicMock()
sys.modules['sentence_transformers'] = MagicMock()
sys.modules['chromadb'] = MagicMock()
sys.modules['psycopg2'] = MagicMock()
sys.modules['psycopg2.extras'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['transformers'] = MagicMock()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing"""
    env_vars = {
        "GROQ_API_KEY": "test_groq_api_key",
        "FSQ_API_KEY": "test_fsq_api_key",
        "FSQ_CLIENT_ID": "test_client_id",
        "FSQ_CLIENT_SECRET": "test_client_secret",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "CHROMA_HOST": "localhost",
        "CHROMA_PORT": "8000"
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


@pytest.fixture
def mock_db_connection():
    """Mock PostgreSQL database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn, mock_cursor


@pytest.fixture
def mock_imap_connection():
    """Mock IMAP connection"""
    mock_imap = MagicMock()
    mock_imap.login.return_value = ('OK', [b'Logged in'])
    mock_imap.select.return_value = ('OK', [b'10'])
    mock_imap.search.return_value = ('OK', [b'1 2 3 4 5'])
    return mock_imap


@pytest.fixture
def sample_email_data():
    """Sample email data for testing"""
    return {
        "subject": "Important Meeting Tomorrow",
        "body": "We have a meeting scheduled for tomorrow at 14:00 at Conference Room A.",
        "sender": "test@tedu.edu.tr",
        "date": "2026-01-15 10:00:00"
    }


@pytest.fixture
def sample_course_data():
    """Sample course data for testing"""
    return {
        "course_code": "CMPE101",
        "course_name": "Introduction to Programming",
        "instructor": "Dr. John Doe",
        "credits": 4,
        "semester": "Fall 2025",
        "description": "Basic programming concepts using Python"
    }


@pytest.fixture
def sample_restaurant_data():
    """Sample restaurant data for testing"""
    return {
        "name": "Campus Cafe",
        "category": "cafe",
        "price_range": "₺₺",
        "distance": 0.5,
        "latitude": 39.9243,
        "longitude": 32.8614
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "title": "Tech Conference 2026",
        "venue": "TED University",
        "event_date": "2026-03-15",
        "price": 50.0,
        "category": "conference"
    }
