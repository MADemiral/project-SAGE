# SAGE Integration Tests with Selenium

Comprehensive end-to-end integration tests for the SAGE frontend application using Selenium WebDriver.

## Overview

These tests validate the entire application flow from the user's perspective, including:
- Authentication flows
- Dashboard interactions
- AI Assistant conversations
- Calendar functionality
- Admin panel features
- Responsive design
- Performance metrics

## Test Structure

```
tests/integration/
├── __init__.py                    # Package initialization
├── conftest.py                    # Pytest fixtures and Selenium setup
├── test_auth_flow.py              # Authentication and session tests
├── test_dashboard.py              # Dashboard and AI assistant tests
├── test_admin_panel.py            # Admin panel functionality tests
├── test_responsive_design.py      # Responsive layout and mobile tests
├── test_performance.py            # Performance and load time tests
└── README.md                      # This file
```

## Prerequisites

### 1. Install Dependencies

```bash
cd backend
pip install selenium webdriver-manager pytest pytest-xdist
```

### 2. Install Chrome/Chromium

The tests use Chrome WebDriver. Ensure Chrome or Chromium is installed:

```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install --cask google-chrome

# The tests will automatically download the appropriate ChromeDriver
```

### 3. Start the Application

Before running tests, ensure both frontend and backend are running:

```bash
# Terminal 1: Start backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Start frontend
cd frontend
npm run dev

# Terminal 3: Run tests (see below)
```

## Running Tests

### Run All Integration Tests

```bash
cd backend
pytest tests/integration/ -v
```

### Run Specific Test Files

```bash
# Authentication tests only
pytest tests/integration/test_auth_flow.py -v

# Dashboard tests only
pytest tests/integration/test_dashboard.py -v

# Admin panel tests only
pytest tests/integration/test_admin_panel.py -v

# Responsive design tests
pytest tests/integration/test_responsive_design.py -v

# Performance tests
pytest tests/integration/test_performance.py -v
```

### Run Tests in Parallel

```bash
# Run tests using 4 workers
pytest tests/integration/ -n 4
```

### Run Tests with Visible Browser (Non-Headless)

By default, tests run in headless mode. To see the browser:

1. Edit `conftest.py` and comment out this line:
   ```python
   # chrome_options.add_argument("--headless")
   ```

2. Run tests:
   ```bash
   pytest tests/integration/ -v
   ```

### Run with Custom Configuration

```bash
# Custom base URL
BASE_URL=http://localhost:3000 pytest tests/integration/ -v

# Custom API URL
API_URL=http://localhost:8080 pytest tests/integration/ -v

# Custom test user credentials
TEST_USER_EMAIL=test@example.com TEST_USER_PASSWORD=pass123 pytest tests/integration/ -v
```

## Environment Variables

Configure tests using environment variables:

```bash
export BASE_URL="http://localhost:5173"          # Frontend URL
export API_URL="http://localhost:8000"           # Backend API URL
export TEST_USER_EMAIL="test@tedu.edu.tr"        # Test user email
export TEST_USER_PASSWORD="testpassword123"      # Test user password
```

Or create a `.env` file in the backend directory:

```env
BASE_URL=http://localhost:5173
API_URL=http://localhost:8000
TEST_USER_EMAIL=test@tedu.edu.tr
TEST_USER_PASSWORD=testpassword123
```

## Test Categories

### 🔐 Authentication Tests (`test_auth_flow.py`)

- ✅ Login page loads
- ✅ Invalid credentials handling
- ✅ Empty field validation
- ✅ Registration page navigation
- ✅ Logout functionality
- ✅ Session persistence
- ✅ Protected route access

### 📊 Dashboard Tests (`test_dashboard.py`)

- ✅ Dashboard layout loads
- ✅ Navigation tabs present
- ✅ Theme toggle functionality
- ✅ Academic Assistant chat
- ✅ Social Assistant chat
- ✅ Message sending
- ✅ Conversation history
- ✅ Calendar integration

### 👥 Admin Panel Tests (`test_admin_panel.py`)

- ✅ Admin access control
- ✅ User list display
- ✅ Add user functionality
- ✅ Search users
- ✅ Theme persistence

### 📱 Responsive Design Tests (`test_responsive_design.py`)

- ✅ Desktop layout (1920x1080)
- ✅ Laptop layout (1366x768)
- ✅ Tablet layout (768x1024)
- ✅ Mobile layout (375x667)
- ✅ Mobile navigation menu
- ✅ Calendar responsive view
- ✅ Chat interface on mobile
- ✅ Image loading
- ✅ JavaScript error detection

### ⚡ Performance Tests (`test_performance.py`)

- ✅ Login page load time (< 5s)
- ✅ Dashboard load time (< 10s)
- ✅ Chat response time (< 15s)
- ✅ Calendar load time (< 8s)
- ✅ Memory leak detection
- ✅ Multiple message handling

## Test Data Requirements

### Create Test Users

Before running tests, create test users in the database:

```bash
# Using the backend API
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@tedu.edu.tr",
    "username": "testuser",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

# Create admin user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tedu.edu.tr",
    "username": "admin",
    "password": "admin123",
    "full_name": "Admin User",
    "is_superuser": true
  }'
```

## Debugging Failed Tests

### 1. Take Screenshots on Failure

Add to `conftest.py`:

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == 'call' and report.failed:
        driver = item.funcargs.get('driver')
        if driver:
            driver.save_screenshot(f'screenshots/{item.name}.png')
```

### 2. View Browser Console Logs

```python
logs = driver.get_log('browser')
for log in logs:
    print(log)
```

### 3. Run Single Test with Output

```bash
pytest tests/integration/test_auth_flow.py::TestAuthenticationFlow::test_login_page_loads -v -s
```

### 4. Use pytest-html for Reports

```bash
pip install pytest-html
pytest tests/integration/ --html=report.html
```

## Common Issues

### Issue: ChromeDriver Version Mismatch

**Solution**: The tests use `webdriver-manager` which automatically downloads the correct ChromeDriver version.

### Issue: "Element not found" Errors

**Solution**: Increase wait times in tests or add explicit waits:

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WebDriverWait(driver, 20).until(
    EC.presence_of_element_located((By.ID, "element-id"))
)
```

### Issue: Tests Fail on CI/CD

**Solution**: Ensure headless mode is enabled and use `--no-sandbox`:

```python
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
```

### Issue: Authentication Tests Fail

**Solution**: Verify test user exists in database and credentials match environment variables.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install selenium webdriver-manager pytest
      
      - name: Start backend
        run: |
          cd backend
          uvicorn app.main:app &
      
      - name: Start frontend
        run: |
          cd frontend
          npm install
          npm run dev &
      
      - name: Wait for services
        run: sleep 10
      
      - name: Run integration tests
        run: |
          cd backend
          pytest tests/integration/ -v
```

## Best Practices

1. **Always use explicit waits** instead of `time.sleep()`
2. **Clean up test data** after each test
3. **Use Page Object Model** for complex tests
4. **Run tests in isolation** - each test should be independent
5. **Mock external APIs** when possible
6. **Use descriptive test names** that explain what's being tested
7. **Add retry logic** for flaky tests
8. **Keep tests fast** - aim for < 1 minute per test file

## Performance Benchmarks

Expected test execution times:

- Authentication tests: ~30 seconds
- Dashboard tests: ~45 seconds
- Admin panel tests: ~25 seconds
- Responsive design tests: ~60 seconds
- Performance tests: ~40 seconds

**Total**: ~3-4 minutes for full suite

## Contributing

When adding new integration tests:

1. Follow existing test structure
2. Use fixtures from `conftest.py`
3. Add descriptive docstrings
4. Handle exceptions gracefully
5. Update this README with new test info

## Troubleshooting

For issues:
1. Check if frontend/backend are running
2. Verify Chrome/ChromeDriver compatibility
3. Check environment variables
4. Review test logs with `-v -s` flags
5. Use non-headless mode for debugging

## Resources

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [Pytest Documentation](https://docs.pytest.org/)
- [WebDriver Manager](https://github.com/SergeyPirogov/webdriver_manager)
