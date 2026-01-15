"""
Unit tests for Foursquare Service
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from app.services.foursquare_service import (
    haversine,
    format_price_range,
    fetch_venues_from_foursquare,
    CAMPUS_LAT,
    CAMPUS_LON
)


class TestFoursquareHelpers:
    """Test helper functions"""
    
    def test_haversine_distance_calculation(self):
        """Test haversine distance calculation"""
        # Distance between campus and a nearby point
        lat1, lon1 = CAMPUS_LAT, CAMPUS_LON
        lat2, lon2 = 39.9250, 32.8620  # ~100m away
        
        distance = haversine(lon1, lat1, lon2, lat2)
        
        assert isinstance(distance, float)
        assert distance > 0
        assert distance < 1  # Should be less than 1 km
    
    def test_haversine_same_location(self):
        """Test haversine with same location (distance should be 0)"""
        distance = haversine(CAMPUS_LON, CAMPUS_LAT, CAMPUS_LON, CAMPUS_LAT)
        assert distance == 0.0
    
    def test_format_price_range_tier_1(self):
        """Test price range formatting for tier 1 (cheap)"""
        result = format_price_range(1)
        assert result == '₺₺'
    
    def test_format_price_range_tier_2(self):
        """Test price range formatting for tier 2 (moderate)"""
        result = format_price_range(2)
        assert result == '₺₺₺'
    
    def test_format_price_range_tier_3(self):
        """Test price range formatting for tier 3 (expensive)"""
        result = format_price_range(3)
        assert result == '₺₺₺₺'
    
    def test_format_price_range_tier_4(self):
        """Test price range formatting for tier 4 (very expensive)"""
        result = format_price_range(4)
        assert result == '₺₺₺₺₺'
    
    def test_format_price_range_invalid(self):
        """Test price range formatting with invalid input"""
        assert format_price_range(0) is None
        assert format_price_range(-1) is None
        assert format_price_range(None) is None
    
    def test_format_price_range_out_of_range(self):
        """Test price range formatting with out of range value"""
        result = format_price_range(5)
        assert result == '₺₺₺'  # Should default to moderate


class TestFoursquareAPI:
    """Test Foursquare API integration"""
    
    @patch('app.services.foursquare_service.requests.get')
    def test_fetch_venues_dining_success(self, mock_get, mock_env_vars):
        """Test successful fetching of dining venues"""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'fsq_id': '123',
                    'name': 'Test Restaurant',
                    'categories': [{'id': '4d4b7105d754a06374d81259', 'name': 'Restaurant'}],
                    'geocodes': {'main': {'latitude': 39.924, 'longitude': 32.861}},
                    'location': {'formatted_address': 'Test Address'},
                    'rating': 8.5,
                    'price': 2
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        venues = fetch_venues_from_foursquare('dining', limit=10)
        
        assert len(venues) > 0
        assert venues[0]['name'] == 'Test Restaurant'
        assert venues[0]['category'] == 'restaurant'
        assert 'distance' in venues[0]
        assert 'price_range' in venues[0]
    
    @patch('app.services.foursquare_service.requests.get')
    def test_fetch_venues_entertainment_success(self, mock_get, mock_env_vars):
        """Test successful fetching of entertainment venues"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'fsq_id': '456',
                    'name': 'Art Gallery',
                    'categories': [{'id': '4bf58dd8d48988d1e2931735', 'name': 'Art Gallery'}],
                    'geocodes': {'main': {'latitude': 39.925, 'longitude': 32.862}},
                    'location': {'formatted_address': 'Gallery Street'},
                    'rating': 9.0
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        venues = fetch_venues_from_foursquare('entertainment', limit=10)
        
        assert len(venues) > 0
        assert venues[0]['name'] == 'Art Gallery'
        assert venues[0]['category'] == 'art_gallery'
    
    @patch('app.services.foursquare_service.requests.get')
    def test_fetch_venues_api_error(self, mock_get, mock_env_vars):
        """Test handling of API errors"""
        mock_get.side_effect = Exception("API Error")
        
        venues = fetch_venues_from_foursquare('dining')
        
        assert venues == []
    
    @patch('app.services.foursquare_service.requests.get')
    def test_fetch_venues_empty_response(self, mock_get, mock_env_vars):
        """Test handling of empty API response"""
        mock_response = MagicMock()
        mock_response.json.return_value = {'results': []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        venues = fetch_venues_from_foursquare('dining')
        
        assert venues == []
    
    @patch('app.services.foursquare_service.requests.get')
    def test_fetch_venues_distance_calculation(self, mock_get, mock_env_vars):
        """Test that distance is calculated correctly"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'fsq_id': '789',
                    'name': 'Nearby Cafe',
                    'categories': [{'id': '63be6904847c3692a84b9bb6', 'name': 'Cafe'}],
                    'geocodes': {'main': {'latitude': 39.925, 'longitude': 32.862}},
                    'location': {'formatted_address': 'Near Campus'},
                    'rating': 8.0,
                    'price': 1
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        venues = fetch_venues_from_foursquare('dining')
        
        assert len(venues) > 0
        assert 'distance' in venues[0]
        assert isinstance(venues[0]['distance'], float)
        assert venues[0]['distance'] >= 0
    
    @patch('app.services.foursquare_service.requests.get')
    def test_fetch_venues_missing_optional_fields(self, mock_get, mock_env_vars):
        """Test handling of venues with missing optional fields"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'results': [
                {
                    'fsq_id': '999',
                    'name': 'Minimal Venue',
                    'categories': [{'id': '4d4b7105d754a06374d81259', 'name': 'Restaurant'}],
                    'geocodes': {'main': {'latitude': 39.924, 'longitude': 32.861}},
                    'location': {'formatted_address': 'Address'}
                    # Missing rating and price
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        venues = fetch_venues_from_foursquare('dining')
        
        assert len(venues) > 0
        assert venues[0]['name'] == 'Minimal Venue'
        # Should handle missing fields gracefully
        assert 'rating' in venues[0]
        assert 'price_range' in venues[0]
