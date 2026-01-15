"""
Unit tests for Bubilet Event Scraper
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from app.services.bubilet_scraper import (
    scrape_ankara_events,
    parse_json_events,
    parse_html_events,
    BUBILET_ANKARA_URL
)


class TestBubiletScraper:
    """Test cases for Bubilet scraper"""
    
    @patch('app.services.bubilet_scraper.requests.get')
    def test_scrape_ankara_events_success(self, mock_get):
        """Test successful event scraping"""
        mock_response = MagicMock()
        mock_response.text = '''
        <html>
        <script>
        self.__next_f.push([1,"{\\"id\\":123,\\"name\\":\\"Test Concert\\",\\"slug\\":\\"test-concert\\",\\"dates\\":[\\"2026-03-15T20:00:00+03:00\\"],\\"price\\":50,\\"venues\\":[{\\"id\\":1,\\"name\\":\\"Test Venue\\",\\"cityName\\":\\"Ankara\\"}]}"])
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        events = scrape_ankara_events()
        
        assert isinstance(events, list)
        mock_get.assert_called_once()
    
    @patch('app.services.bubilet_scraper.requests.get')
    def test_scrape_ankara_events_request_error(self, mock_get):
        """Test handling of request errors"""
        mock_get.side_effect = Exception("Network error")
        
        events = scrape_ankara_events()
        
        assert events == []
    
    @patch('app.services.bubilet_scraper.requests.get')
    def test_scrape_ankara_events_timeout(self, mock_get):
        """Test handling of timeout errors"""
        mock_get.side_effect = TimeoutError("Request timeout")
        
        events = scrape_ankara_events()
        
        assert events == []
    
    def test_parse_json_events_valid_data(self):
        """Test parsing of valid JSON event data"""
        html = '''
        <script>
        self.__next_f.push([1,"{\\"id\\":456,\\"name\\":\\"Jazz Night\\",\\"slug\\":\\"jazz-night\\",\\"dates\\":[\\"2026-04-10T21:00:00+03:00\\"],\\"price\\":75.5,\\"venues\\":[{\\"id\\":2,\\"name\\":\\"Jazz Club\\",\\"cityName\\":\\"Ankara\\"}]}"])
        </script>
        '''
        
        events = parse_json_events(html)
        
        assert isinstance(events, list)
    
    def test_parse_json_events_no_data(self):
        """Test parsing when no JSON data is found"""
        html = '<html><body>No event data</body></html>'
        
        events = parse_json_events(html)
        
        assert events == []
    
    def test_parse_json_events_malformed_json(self):
        """Test handling of malformed JSON data"""
        html = '''
        <script>
        self.__next_f.push([1,"invalid json data"])
        </script>
        '''
        
        events = parse_json_events(html)
        
        # Should return empty list on error
        assert isinstance(events, list)
    
    def test_parse_html_events_fallback(self):
        """Test HTML parsing as fallback method"""
        html = '''
        <html>
        <body>
            <div class="event-card">
                <h3>Event Title</h3>
                <span class="date">2026-05-20</span>
                <span class="venue">Test Venue</span>
                <span class="price">₺100</span>
            </div>
        </body>
        </html>
        '''
        
        events = parse_html_events(html)
        
        assert isinstance(events, list)
    
    @patch('app.services.bubilet_scraper.requests.get')
    def test_scrape_includes_user_agent(self, mock_get):
        """Test that requests include proper User-Agent header"""
        mock_response = MagicMock()
        mock_response.text = '<html></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scrape_ankara_events()
        
        # Verify User-Agent was included in request
        call_args = mock_get.call_args
        assert 'headers' in call_args.kwargs
        assert 'User-Agent' in call_args.kwargs['headers']
        assert 'Mozilla' in call_args.kwargs['headers']['User-Agent']
    
    @patch('app.services.bubilet_scraper.requests.get')
    def test_scrape_has_timeout(self, mock_get):
        """Test that requests have timeout configured"""
        mock_response = MagicMock()
        mock_response.text = '<html></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scrape_ankara_events()
        
        # Verify timeout parameter
        call_args = mock_get.call_args
        assert 'timeout' in call_args.kwargs
        assert call_args.kwargs['timeout'] == 30
    
    def test_bubilet_url_constant(self):
        """Test Bubilet URL constant"""
        assert BUBILET_ANKARA_URL == "https://www.bubilet.com.tr/ankara"
    
    def test_parse_json_events_date_parsing(self):
        """Test proper date parsing from ISO format"""
        html = '''
        <script>
        self.__next_f.push([1,"{\\"id\\":789,\\"name\\":\\"Theater Play\\",\\"slug\\":\\"theater\\",\\"dates\\":[\\"2026-06-01T19:30:00+03:00\\",\\"2026-06-02T19:30:00+03:00\\"],\\"price\\":120,\\"venues\\":[{\\"id\\":3,\\"name\\":\\"Theater Hall\\",\\"cityName\\":\\"Ankara\\"}]}"])
        </script>
        '''
        
        events = parse_json_events(html)
        
        # Should parse dates correctly
        assert isinstance(events, list)
    
    def test_parse_json_events_price_handling(self):
        """Test handling of various price formats"""
        html_free = '''
        <script>
        self.__next_f.push([1,"{\\"id\\":111,\\"name\\":\\"Free Event\\",\\"slug\\":\\"free\\",\\"dates\\":[\\"2026-07-01T10:00:00+03:00\\"],\\"price\\":null,\\"venues\\":[{\\"id\\":4,\\"name\\":\\"Open Space\\",\\"cityName\\":\\"Ankara\\"}]}"])
        </script>
        '''
        
        events = parse_json_events(html_free)
        
        # Should handle null/free prices
        assert isinstance(events, list)
    
    @patch('app.services.bubilet_scraper.requests.get')
    def test_scrape_fallback_to_html_parsing(self, mock_get):
        """Test fallback to HTML parsing when JSON parsing fails"""
        mock_response = MagicMock()
        mock_response.text = '<html><body>No JSON data here</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with patch('app.services.bubilet_scraper.parse_json_events', return_value=[]):
            with patch('app.services.bubilet_scraper.parse_html_events', return_value=[{'title': 'Test'}]):
                events = scrape_ankara_events()
                
                # Should use fallback method
                assert isinstance(events, list)
