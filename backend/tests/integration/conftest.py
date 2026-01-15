"""
Pytest configuration for integration tests with Selenium
"""
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application"""
    return os.getenv("BASE_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def api_url():
    """API base URL"""
    return os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture(scope="function")
def driver(base_url):
    """
    Create a Chrome WebDriver instance for each test
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Initialize the driver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)  # Wait up to 10 seconds for elements
    
    yield driver
    
    # Cleanup
    driver.quit()


@pytest.fixture(scope="function")
def authenticated_driver(driver, base_url):
    """
    Create an authenticated driver with a logged-in session
    """
    # Navigate to login page
    driver.get(f"{base_url}/login")
    time.sleep(2)
    
    # Perform login (you may need to adjust selectors)
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    try:
        # Wait for login form
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
        )
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        # Enter credentials (use test credentials)
        test_email = os.getenv("TEST_USER_EMAIL", "test@tedu.edu.tr")
        test_password = os.getenv("TEST_USER_PASSWORD", "testpassword123")
        
        email_input.send_keys(test_email)
        password_input.send_keys(test_password)
        
        # Click login button
        login_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for redirect to dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/")
        )
        
        time.sleep(2)  # Wait for page to fully load
        
    except Exception as e:
        print(f"Authentication failed: {e}")
        # Continue anyway for tests that don't require auth
    
    yield driver


@pytest.fixture
def test_user():
    """Test user credentials"""
    return {
        "email": "test@tedu.edu.tr",
        "password": "testpassword123",
        "username": "testuser"
    }


@pytest.fixture
def admin_user():
    """Admin user credentials"""
    return {
        "email": "admin@tedu.edu.tr",
        "password": "admin123",
        "username": "admin"
    }
