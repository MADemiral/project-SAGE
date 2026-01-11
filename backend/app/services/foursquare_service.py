"""
Service for fetching restaurant and entertainment venue data from Foursquare API
"""
import os
import requests
import logging
from typing import List, Dict, Any
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)

# Zümrüt Evler Kolej Campus coordinates
CAMPUS_LAT = 39.92424862995977
CAMPUS_LON = 32.861328748007665
CAMPUS_NAME = "Kolej Campus"

# Foursquare API configuration (v3 Places API)
FOURSQUARE_API_KEY = os.getenv("FSQ_API_KEY")  # Bearer token for v3 API
FOURSQUARE_CLIENT_ID = os.getenv("FSQ_CLIENT_ID")
FOURSQUARE_CLIENT_SECRET = os.getenv("FSQ_CLIENT_SECRET")

# Category IDs for filtering
DINING_CATEGORIES = [
    "4d4b7105d754a06374d81259",  # Restaurant
    "63be6904847c3692a84b9bb6",  # Cafe, Coffee, and Tea House
    "4bf58dd8d48988d1d0941735",  # Dessert Shop
    "4bf58dd8d48988d128941735",  # Cafeteria
    "63be6904847c3692a84b9bb5",  # Dining and Drinking
]

ENTERTAINMENT_CATEGORIES = [
    "4bf58dd8d48988d1e1931735",  # Arcade
    "4bf58dd8d48988d1e2931735",  # Art Gallery
]

# Category ID to readable name mapping
CATEGORY_NAMES = {
    "4d4b7105d754a06374d81259": "restaurant",
    "63be6904847c3692a84b9bb6": "cafe",
    "4bf58dd8d48988d1d0941735": "dessert_shop",
    "4bf58dd8d48988d128941735": "cafeteria",
    "63be6904847c3692a84b9bb5": "dining_drinking",
    "4bf58dd8d48988d1e1931735": "arcade",
    "4bf58dd8d48988d1e2931735": "art_gallery",
}


def haversine(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # Radius of earth in kilometers
    return c * r


def format_price_range(price_tier: int) -> str:
    """
    Convert Foursquare price tier (1-4) to Turkish Lira symbols (₺)
    Returns string like '₺', '₺₺', '₺₺₺', '₺₺₺₺', '₺₺₺₺₺'
    Maps to 5-point scale:
    - tier 1 (cheap) -> ₺ or ₺₺
    - tier 2 (moderate) -> ₺₺₺
    - tier 3 (expensive) -> ₺₺₺₺
    - tier 4 (very expensive) -> ₺₺₺₺₺
    """
    if not price_tier or price_tier < 1:
        return None
    
    # Map Foursquare's 1-4 scale to our 1-5 scale
    price_map = {
        1: '₺₺',      # Cheap
        2: '₺₺₺',     # Moderate
        3: '₺₺₺₺',    # Expensive
        4: '₺₺₺₺₺'    # Very Expensive
    }
    
    return price_map.get(price_tier, '₺₺₺')  # Default to moderate


def fetch_venues_from_foursquare(
    venue_type: str = "dining",
    limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch venues from Foursquare API using OAuth credentials
    Fetches limit venues for EACH category separately
    
    Args:
        venue_type: Type of venues to fetch - "dining" or "entertainment"
        limit: Maximum number of results PER CATEGORY (default: 50)
        
    Returns:
        List of venue dictionaries with Foursquare data
    """
    
    if not FOURSQUARE_CLIENT_ID or not FOURSQUARE_CLIENT_SECRET:
        logger.error("Foursquare OAuth credentials not found in environment variables")
        return []
    
    # Select categories based on venue type
    if venue_type == "dining":
        categories = DINING_CATEGORIES
    elif venue_type == "entertainment":
        categories = ENTERTAINMENT_CATEGORIES
    else:
        logger.error(f"Invalid venue type: {venue_type}")
        return []
    
    all_venues = []
    # We want to store same venue multiple times with different category labels
    # So don't deduplicate here - let database handle it with composite key
    
    # Fetch venues for each category separately
    for category_id in categories:
        category_name = CATEGORY_NAMES.get(category_id, category_id)
        logger.info(f"Fetching {limit} venues for category: {category_name} ({category_id})...")
        
        # Build query parameters for v3 Places API
        params = {
            "ll": f"{CAMPUS_LAT},{CAMPUS_LON}",
            "fsq_category_ids": category_id,  # Category filter (correct parameter name)
            "limit": limit,
            "sort": "DISTANCE",  # Sort by distance (no radius limit)
        }
        
        # Use v3 Places API endpoint
        search_url = "https://places-api.foursquare.com/places/search"
        
        # Set headers for v3 API with Bearer token
        headers = {
            'accept': 'application/json',
            'authorization': f'Bearer {FOURSQUARE_API_KEY}',
            'X-Places-Api-Version': '2025-06-17'
        }
        
        try:
            response = requests.get(search_url, params=params, headers=headers, timeout=30)
            
            # Log response details for debugging
            if response.status_code != 200:
                logger.error(f"API Response Status: {response.status_code}")
                logger.error(f"API Response Body: {response.text}")
                continue
            
            response.raise_for_status()
            
            data = response.json()
            # v3 API returns results directly, not nested in 'response'
            venues_list = data.get('results', [])
            
            logger.info(f"  -> Found {len(venues_list)} venues for {category_name}")
            
            for venue in venues_list:
                # Parse v3 API venue format with the requested category
                # Don't skip duplicates - same venue will be stored with different categories
                venue_data = parse_foursquare_venue_v3(venue, requested_category=category_name)
                all_venues.append(venue_data)
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {category_name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing {category_name}: {e}")
            continue
    
    logger.info(f"Total unique {venue_type} venues fetched: {len(all_venues)}")
    return all_venues


def parse_foursquare_venue_v3(venue: Dict[str, Any], requested_category: str = None) -> Dict[str, Any]:
    """Parse a Foursquare v3 Places API venue result into our format
    
    Args:
        venue: Foursquare v3 Places API venue object
        requested_category: The category we requested (e.g., 'restaurant', 'cafe')
    """
    
    # Extract location data - v3 has lat/lon directly on venue, OR distance if provided
    lat = venue.get('latitude')
    lon = venue.get('longitude')
    
    # Use distance from API if available (in meters), convert to km
    distance = venue.get('distance')
    if distance is not None:
        distance = round(distance / 1000, 2)  # Convert meters to km
    elif lat and lon:
        # Calculate distance if not provided
        distance = haversine(CAMPUS_LON, CAMPUS_LAT, lon, lat)
        distance = round(distance, 2)
    
    # Get primary category - v3 uses fsq_category_id
    categories = venue.get('categories', [])
    primary_category = categories[0] if categories else {}
    category_id = primary_category.get('fsq_category_id')  # v3 field name
    
    # Use requested category if provided, otherwise detect from venue
    if requested_category:
        category_name = requested_category
    else:
        category_name = CATEGORY_NAMES.get(category_id, 'other')
    
    # Get all category names
    category_list = [cat.get('name', '') for cat in categories]
    
    # Extract location details
    location = venue.get('location', {})
    address_parts = []
    if location.get('address'):
        address_parts.append(location['address'])
    if location.get('locality'):
        address_parts.append(location['locality'])
    if location.get('region'):
        address_parts.append(location['region'])
    
    formatted_address = ', '.join(address_parts) if address_parts else None
    
    venue_data = {
        'name': venue.get('name', 'Unnamed'),
        'category': category_name,
        'categories': category_list,
        'fsq_id': venue.get('fsq_place_id'),  # v3 uses fsq_place_id
        'latitude': lat,
        'longitude': lon,
        'distance_from_campus': distance,
        'address': formatted_address,
        'locality': location.get('locality'),
        'region': location.get('region'),
        'postcode': location.get('postcode'),
        'country': location.get('country', 'TR'),
        'phone': venue.get('tel'),
        'website': venue.get('website'),
        'email': venue.get('email'),
        'description': venue.get('description'),
        'rating': venue.get('rating'),
        'price': format_price_range(venue.get('price')) if venue.get('price') else None,
        'opening_hours': None,  # Would need separate details call
        'photos': [],  # Would need separate photos call
        'tags': extract_tags_v3(venue),
        'verified': venue.get('verified', False),
        'hours': venue.get('hours', {})
    }
    
    return venue_data


def extract_tags_v3(venue: Dict[str, Any]) -> List[str]:
    """Extract useful tags from v3 API venue data"""
    tags = []
    
    # Add verified status
    if venue.get('verified'):
        tags.append('verified')
    
    # Add category tags
    for cat in venue.get('categories', []):
        if cat.get('name'):
            tags.append(cat['name'].lower())
    
    # Add features/amenities
    if venue.get('features'):
        features = venue['features']
        if features.get('payment', {}).get('credit_cards'):
            tags.append('credit_cards')
        if features.get('food_and_drink', {}).get('alcohol'):
            tags.append('alcohol')
        if features.get('amenities', {}).get('wifi'):
            tags.append('wifi')
        if features.get('amenities', {}).get('parking'):
            tags.append('parking')
    
    return tags


def parse_foursquare_venue_v2(venue: Dict[str, Any], requested_category: str = None) -> Dict[str, Any]:
    """Parse a Foursquare v2 API venue result into our format
    
    Args:
        venue: Foursquare v2 API venue object
        requested_category: The category we requested (e.g., 'restaurant', 'cafe')
    """
    
    # Extract location data
    location = venue.get('location', {})
    lat = location.get('lat')
    lon = location.get('lng')
    
    # Calculate distance from campus
    distance = None
    if lat and lon:
        distance = haversine(CAMPUS_LON, CAMPUS_LAT, lon, lat)
        distance = round(distance, 2)
    
    # Get primary category
    categories = venue.get('categories', [])
    primary_category = categories[0] if categories else {}
    category_id = primary_category.get('id')
    
    # Use requested category if provided, otherwise detect from venue
    if requested_category:
        category_name = requested_category
    else:
        category_name = CATEGORY_NAMES.get(category_id, 'other')
    
    # Get all category names
    category_list = [cat.get('name', '') for cat in categories]
    
    # Extract location details
    address_parts = []
    if location.get('address'):
        address_parts.append(location['address'])
    if location.get('city'):
        address_parts.append(location['city'])
    if location.get('state'):
        address_parts.append(location['state'])
    
    formatted_address = ', '.join(address_parts) if address_parts else None
    
    # Get venue stats if available
    stats = venue.get('stats', {})
    
    venue_data = {
        'name': venue.get('name', 'Unnamed'),
        'category': category_name,
        'categories': category_list,
        'fsq_id': venue.get('id'),  # v2 uses 'id' not 'fsq_id'
        'latitude': lat,
        'longitude': lon,
        'distance_from_campus': distance,
        'address': formatted_address,
        'locality': location.get('city'),
        'region': location.get('state'),
        'postcode': location.get('postalCode'),
        'country': location.get('country', 'TR'),
        'phone': venue.get('contact', {}).get('phone'),
        'website': venue.get('url'),
        'email': None,  # v2 API doesn't provide email
        'description': None,  # Would need separate venue details call
        'rating': venue.get('rating'),  # v2 has rating directly
        'price': format_price_range(venue.get('price', {}).get('tier')) if 'price' in venue else None,
        'opening_hours': None,  # Would need separate venue details call
        'photos': [],  # Would need separate photos call
        'tags': extract_tags_v2(venue),
        'checkins': stats.get('checkinsCount'),
        'users': stats.get('usersCount'),
    }
    
    return venue_data


def extract_tags_v2(venue: Dict[str, Any]) -> List[str]:
    """Extract relevant tags from v2 venue data"""
    tags = []
    
    # Add price level as tag
    price = venue.get('price', {}).get('tier')
    if price:
        tags.append(f'price_level_{price}')
    
    # Add rating as tag if available
    rating = venue.get('rating')
    if rating and rating >= 8.0:
        tags.append('highly_rated')
    
    # Add verified tag if venue is verified
    if venue.get('verified'):
        tags.append('verified')
    
    return tags


def parse_foursquare_venue(result: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a Foursquare venue result into our format"""
    
    # Extract location data
    geocodes = result.get('geocodes', {}).get('main', {})
    lat = geocodes.get('latitude')
    lon = geocodes.get('longitude')
    
    # Calculate distance from campus
    distance = None
    if lat and lon:
        distance = haversine(CAMPUS_LON, CAMPUS_LAT, lon, lat)
        distance = round(distance, 2)
    
    # Get primary category
    categories = result.get('categories', [])
    primary_category = categories[0] if categories else {}
    category_id = primary_category.get('id')
    category_name = CATEGORY_NAMES.get(category_id, 'other')
    
    # Get all category names
    category_list = [cat.get('name', '') for cat in categories]
    
    # Extract location details
    location = result.get('location', {})
    address_parts = []
    if location.get('address'):
        address_parts.append(location['address'])
    if location.get('locality'):
        address_parts.append(location['locality'])
    if location.get('region'):
        address_parts.append(location['region'])
    
    formatted_address = ', '.join(address_parts) if address_parts else None
    
    # Extract opening hours
    hours = result.get('hours', {})
    opening_hours = None
    if hours:
        opening_hours = {
            'display': hours.get('display'),
            'is_open_now': hours.get('open_now'),
            'regular': hours.get('regular', [])
        }
    
    # Extract photos
    photos = result.get('photos', [])
    photo_urls = []
    for photo in photos[:3]:  # Get up to 3 photos
        prefix = photo.get('prefix', '')
        suffix = photo.get('suffix', '')
        if prefix and suffix:
            # Build photo URL with medium size
            photo_url = f"{prefix}300x300{suffix}"
            photo_urls.append(photo_url)
    
    venue_data = {
        'name': result.get('name', 'Unnamed'),
        'category': category_name,
        'categories': category_list,
        'fsq_id': result.get('fsq_id'),
        'latitude': lat,
        'longitude': lon,
        'distance_from_campus': distance,
        'address': formatted_address,
        'locality': location.get('locality'),
        'region': location.get('region'),
        'postcode': location.get('postcode'),
        'country': location.get('country', 'TR'),
        'phone': result.get('tel'),
        'website': result.get('website'),
        'email': result.get('email'),
        'description': result.get('description'),
        'rating': result.get('rating'),
        'price': result.get('price'),
        'opening_hours': opening_hours,
        'photos': photo_urls,
        'tags': extract_tags(result),
    }
    
    return venue_data


def extract_tags(venue: Dict[str, Any]) -> List[str]:
    """Extract relevant tags from venue data"""
    tags = []
    
    # Check if venue is open now
    hours = venue.get('hours', {})
    if hours.get('open_now'):
        tags.append('open_now')
    
    # Add price level as tag
    price = venue.get('price')
    if price:
        tags.append(f'price_level_{price}')
    
    # Add rating as tag if available
    rating = venue.get('rating')
    if rating and rating >= 8.0:
        tags.append('highly_rated')
    
    return tags


def fetch_restaurants_from_foursquare(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch dining venues
    
    Args:
        limit: Maximum number of results (default: 50)
        
    Returns:
        List of restaurant/cafe dictionaries
    """
    return fetch_venues_from_foursquare(venue_type="dining", limit=limit)


def fetch_entertainment_from_foursquare(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Convenience function to fetch entertainment venues
    
    Args:
        limit: Maximum number of results (default: 50)
        
    Returns:
        List of entertainment venue dictionaries
    """
    return fetch_venues_from_foursquare(venue_type="entertainment", limit=limit)
