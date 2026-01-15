# SAGE Backend Tests

Comprehensive unit tests for SAGE backend services.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── pytest.ini               # Pytest settings
├── test_groq_service.py     # Tests for Academic and Social AI assistants
├── test_foursquare_service.py  # Tests for Foursquare venue fetching
├── test_imap_service.py     # Tests for IMAP email service
└── test_bubilet_scraper.py  # Tests for Bubilet event scraper
```

## Running Tests

### Install Test Dependencies

First, install the required testing packages:

```bash
cd backend
pip install pytest pytest-cov pytest-mock pytest-asyncio
```

### Run All Tests

```bash
# From backend directory
pytest

# With verbose output
pytest -v

# With coverage report
pytest --cov=app --cov-report=html
```

### Run Specific Test Files

```bash
# Test only Groq service
pytest tests/test_groq_service.py

# Test only Foursquare service
pytest tests/test_foursquare_service.py

# Test only IMAP service
pytest tests/test_imap_service.py

# Test only Bubilet scraper
pytest tests/test_bubilet_scraper.py
```

### Run Specific Test Classes or Methods

```bash
# Run specific test class
pytest tests/test_groq_service.py::TestGroqAcademicService

# Run specific test method
pytest tests/test_groq_service.py::TestGroqAcademicService::test_detect_language_turkish
```

### Run Tests with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only fast tests (exclude slow tests)
pytest -m "not slow"
```

## Test Coverage

View coverage report after running tests with `--cov`:

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## What's Tested

### GroqService (`test_groq_service.py`)
- ✅ Academic Assistant initialization
- ✅ Social Assistant initialization
- ✅ Language detection (Turkish/English)
- ✅ Project context retrieval
- ✅ Course context with embeddings
- ✅ Restaurant context retrieval
- ✅ Event context retrieval
- ✅ Response generation
- ✅ Error handling for database issues
- ✅ ChromaDB integration

### FoursquareService (`test_foursquare_service.py`)
- ✅ Haversine distance calculation
- ✅ Price range formatting
- ✅ Dining venue fetching
- ✅ Entertainment venue fetching
- ✅ API error handling
- ✅ Empty response handling
- ✅ Distance calculations
- ✅ Missing optional fields handling

### IMAPService (`test_imap_service.py`)
- ✅ IMAP connection establishment
- ✅ Authentication (success and failure)
- ✅ Connection error handling (EOF, timeout)
- ✅ Email fetching
- ✅ Connection expiration handling
- ✅ Event extraction from emails
- ✅ Logout and cleanup
- ✅ Reconnection logic

### BubiletScraper (`test_bubilet_scraper.py`)
- ✅ Event scraping from Ankara page
- ✅ JSON event data parsing
- ✅ HTML fallback parsing
- ✅ Network error handling
- ✅ Timeout handling
- ✅ User-Agent configuration
- ✅ Date/price parsing
- ✅ Malformed data handling

## Mocking Strategy

Tests use mocking to isolate services and avoid external dependencies:

- **Database**: PostgreSQL connections mocked with `psycopg2.connect`
- **External APIs**: HTTP requests mocked with `requests.get`
- **IMAP**: Email connections mocked with `imaplib.IMAP4_SSL`
- **LLM**: Groq API calls mocked with `Groq` client
- **Embeddings**: SentenceTransformer mocked
- **Vector DB**: ChromaDB mocked

## Writing New Tests

### Test Template

```python
import pytest
from unittest.mock import Mock, patch
from app.services.your_service import YourService


class TestYourService:
    """Test cases for YourService"""
    
    def test_method_success(self, mock_env_vars):
        """Test successful method execution"""
        service = YourService()
        result = service.your_method()
        
        assert result is not None
        # Add assertions
    
    def test_method_error_handling(self):
        """Test error handling"""
        service = YourService()
        
        with pytest.raises(Exception) as exc_info:
            service.your_method()
        
        assert "error message" in str(exc_info.value)
```

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    cd backend
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./backend/coverage.xml
```

## Troubleshooting

### Import Errors
If you get import errors, ensure you're running pytest from the `backend` directory:
```bash
cd backend
pytest
```

### Missing Dependencies
Install all test dependencies:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-mock
```

### Mock Issues
If mocks aren't working, check the patch path matches the import in the actual code:
```python
# If code has: from app.services import groq_service
# Use: @patch('app.services.groq_service.Groq')
```

## Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** describing what's being tested
3. **Use fixtures** for reusable test data
4. **Mock external dependencies** to keep tests fast and isolated
5. **Test both success and failure paths**
6. **Keep tests independent** - no shared state
7. **Use parametrize** for testing multiple inputs
8. **Document complex test setups** with comments

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain >80% code coverage
4. Update this README if adding new test files
