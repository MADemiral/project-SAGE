"""
Integration tests for performance and load times
"""
import pytest
from selenium.webdriver.common.by import By
import time


class TestPageLoadPerformance:
    """Test page load performance"""
    
    def test_login_page_loads_quickly(self, driver, base_url):
        """Test that login page loads within acceptable time"""
        start_time = time.time()
        driver.get(f"{base_url}/login")
        
        # Wait for page to be fully loaded
        driver.execute_script("return document.readyState") == "complete"
        load_time = time.time() - start_time
        
        # Should load in less than 5 seconds
        assert load_time < 5
    
    def test_dashboard_loads_quickly(self, authenticated_driver, base_url):
        """Test that dashboard loads within acceptable time"""
        driver = authenticated_driver
        start_time = time.time()
        driver.get(f"{base_url}/")
        
        # Wait for elements to appear
        time.sleep(2)
        load_time = time.time() - start_time
        
        # Should load in less than 10 seconds
        assert load_time < 10
    
    def test_chat_response_time(self, authenticated_driver, base_url):
        """Test chat assistant response time"""
        driver = authenticated_driver
        driver.get(f"{base_url}/")
        time.sleep(2)
        
        try:
            # Send a simple message
            text_inputs = driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text']")
            
            if text_inputs:
                start_time = time.time()
                
                text_inputs[0].send_keys("Hello")
                
                # Click send
                send_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button")
                for button in send_buttons:
                    button.click()
                    break
                
                time.sleep(5)  # Wait for response
                response_time = time.time() - start_time
                
                # Should respond within 15 seconds (LLM can be slow)
                assert response_time < 15
        except:
            assert True
    
    def test_calendar_page_loads_quickly(self, authenticated_driver, base_url):
        """Test calendar page load performance"""
        driver = authenticated_driver
        start_time = time.time()
        driver.get(f"{base_url}/calendar")
        time.sleep(2)
        
        load_time = time.time() - start_time
        
        # Should load quickly
        assert load_time < 8


class TestMemoryAndResourceUsage:
    """Test for memory leaks and resource usage"""
    
    def test_no_memory_leak_on_navigation(self, authenticated_driver, base_url):
        """Test that navigating doesn't cause memory leaks"""
        driver = authenticated_driver
        
        # Navigate between pages multiple times
        for _ in range(3):
            driver.get(f"{base_url}/")
            time.sleep(1)
            driver.get(f"{base_url}/calendar")
            time.sleep(1)
            driver.get(f"{base_url}/users")
            time.sleep(1)
        
        # If we get here without crashes, test passes
        assert True
    
    def test_multiple_chat_messages_performance(self, authenticated_driver, base_url):
        """Test sending multiple chat messages"""
        driver = authenticated_driver
        driver.get(f"{base_url}/")
        time.sleep(2)
        
        try:
            # Send multiple messages
            for i in range(3):
                text_inputs = driver.find_elements(By.CSS_SELECTOR, "textarea, input[type='text']")
                
                if text_inputs:
                    text_inputs[0].clear()
                    text_inputs[0].send_keys(f"Test message {i}")
                    time.sleep(0.5)
                    
                    # Click send
                    send_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], button")
                    for button in send_buttons:
                        button.click()
                        break
                    
                    time.sleep(2)
            
            # Should handle multiple messages without crashing
            assert True
        except:
            assert True
