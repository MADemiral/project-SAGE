"""
Service for fetching restaurant data from OpenStreetMap using Overpass API
"""
import os
import requests
import logging
from typing import List, Dict, Any
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)

# Default TED University coordinates (user-provided). These can be overridden
# with environment variables OVERPASS_CENTER_LAT and OVERPASS_CENTER_LON.
DEFAULT_TED_UNIVERSITY_LAT = 39.92418980690654
DEFAULT_TED_UNIVERSITY_LON = 32.8611959151203

# Read overrides from environment if provided (keeps floats safe)
try:
    TED_UNIVERSITY_LAT = float(os.getenv("OVERPASS_CENTER_LAT", DEFAULT_TED_UNIVERSITY_LAT))
except (TypeError, ValueError):
    TED_UNIVERSITY_LAT = DEFAULT_TED_UNIVERSITY_LAT

try:
    TED_UNIVERSITY_LON = float(os.getenv("OVERPASS_CENTER_LON", DEFAULT_TED_UNIVERSITY_LON))
except (TypeError, ValueError):
    TED_UNIVERSITY_LON = DEFAULT_TED_UNIVERSITY_LON

# Optional radius override (in km) for around queries when use_ankara_bbox=False
try:
    DEFAULT_OVERPASS_RADIUS_KM = float(os.getenv("OVERPASS_RADIUS_KM", "5.0"))
except (TypeError, ValueError):
    DEFAULT_OVERPASS_RADIUS_KM = 5.0

# Overpass API endpoint
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"


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


def fetch_restaurants_from_osm(radius_km: float = 5.0, use_ankara_bbox: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch restaurants, cafes, and fast food places from OpenStreetMap
    
    Args:
        radius_km: Search radius in kilometers (default: 5km) - used only if use_ankara_bbox=False
        use_ankara_bbox: If True, fetch all restaurants in Ankara city (default: True)
        
    Returns:
        List of restaurant dictionaries with OSM data
    """
    
    if use_ankara_bbox:
        # Ankara bounding box (approximate)
        # South-West: 39.7, 32.5
        # North-East: 40.1, 33.0
        query = """
        [out:json][timeout:60];
        (
          node["amenity"="restaurant"](39.7,32.5,40.1,33.0);
          way["amenity"="restaurant"](39.7,32.5,40.1,33.0);
          node["amenity"="cafe"](39.7,32.5,40.1,33.0);
          way["amenity"="cafe"](39.7,32.5,40.1,33.0);
          node["amenity"="fast_food"](39.7,32.5,40.1,33.0);
          way["amenity"="fast_food"](39.7,32.5,40.1,33.0);
          node["amenity"="bar"](39.7,32.5,40.1,33.0);
          way["amenity"="bar"](39.7,32.5,40.1,33.0);
          node["amenity"="pub"](39.7,32.5,40.1,33.0);
          way["amenity"="pub"](39.7,32.5,40.1,33.0);
        );
        out body center;
        """
        logger.info(f"Fetching all restaurants in Ankara city...")
    else:
        # If caller didn't pass a radius, allow an env override default
        if radius_km is None:
            radius_km = DEFAULT_OVERPASS_RADIUS_KM

        # Convert km to meters for Overpass API
        radius_meters = int(radius_km * 1000)
        
        # Overpass QL query to find restaurants, cafes, and fast food
        query = f"""
        [out:json][timeout:30];
        (
          node["amenity"="restaurant"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          way["amenity"="restaurant"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          node["amenity"="cafe"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          way["amenity"="cafe"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          node["amenity"="fast_food"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          way["amenity"="fast_food"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          node["amenity"="bar"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          way["amenity"="bar"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          node["amenity"="pub"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
          way["amenity"="pub"](around:{radius_meters},{TED_UNIVERSITY_LAT},{TED_UNIVERSITY_LON});
        );
        out body center;
        """
    logger.info(f"Fetching restaurants within {radius_km}km of TED University at ({TED_UNIVERSITY_LAT}, {TED_UNIVERSITY_LON})...")
    
    try:
        response = requests.post(OVERPASS_API_URL, data={'data': query}, timeout=90)
        response.raise_for_status()
        
        data = response.json()
        elements = data.get('elements', [])
        
        restaurants = []
        for element in elements:
            tags = element.get('tags', {})
            
            # Get coordinates (handle both nodes and ways)
            if 'lat' in element and 'lon' in element:
                lat = element['lat']
                lon = element['lon']
            elif 'center' in element:
                lat = element['center']['lat']
                lon = element['center']['lon']
            else:
                continue
            
            # Calculate distance from campus
            distance = haversine(TED_UNIVERSITY_LON, TED_UNIVERSITY_LAT, lon, lat)
            
            # Extract restaurant information
            restaurant_data = {
                'name': tags.get('name', 'Unnamed'),
                'category': tags.get('amenity', 'restaurant'),
                'cuisine_type': tags.get('cuisine'),
                'address': format_address(tags),
                'latitude': lat,
                'longitude': lon,
                'phone': tags.get('phone') or tags.get('contact:phone'),
                'website': tags.get('website') or tags.get('contact:website'),
                'opening_hours': parse_opening_hours(tags.get('opening_hours')),
                'description': tags.get('description'),
                'osm_id': f"{element['type']}/{element['id']}",
                'distance_from_campus': round(distance, 2),
                'tags': extract_tags(tags),
                'rating': None,  # OSM doesn't provide ratings
                'price_range': None  # OSM doesn't provide price ranges
            }
            
            restaurants.append(restaurant_data)
        
        logger.info(f"Found {len(restaurants)} restaurants")
        return restaurants
        
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Overpass API: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error processing OSM data: {e}")
        return []


def format_address(tags: Dict[str, str]) -> str:
    """Format address from OSM tags"""
    address_parts = []
    
    if 'addr:street' in tags:
        street = tags['addr:street']
        if 'addr:housenumber' in tags:
            street = f"{tags['addr:housenumber']} {street}"
        address_parts.append(street)
    
    if 'addr:suburb' in tags:
        address_parts.append(tags['addr:suburb'])
    
    if 'addr:city' in tags:
        address_parts.append(tags['addr:city'])
    elif 'addr:province' in tags:
        address_parts.append(tags['addr:province'])
    
    return ', '.join(address_parts) if address_parts else None


def parse_opening_hours(opening_hours_str: str) -> Dict[str, Any]:
    """
    Parse OSM opening hours format (simplified version)
    Returns a simple dict structure
    """
    if not opening_hours_str:
        return None
    
    # For now, just store the raw string
    # A full parser would need to handle complex OSM opening_hours syntax
    return {
        'raw': opening_hours_str,
        'format': 'OSM'
    }


def extract_tags(tags: Dict[str, str]) -> List[str]:
    """Extract relevant tags for filtering"""
    tag_list = []
    
    # Dietary options
    if tags.get('diet:vegetarian') == 'yes':
        tag_list.append('vegetarian')
    if tags.get('diet:vegan') == 'yes':
        tag_list.append('vegan')
    if tags.get('diet:halal') == 'yes':
        tag_list.append('halal')
    if tags.get('diet:kosher') == 'yes':
        tag_list.append('kosher')
    
    # Features
    if tags.get('outdoor_seating') == 'yes':
        tag_list.append('outdoor_seating')
    if tags.get('wifi') == 'yes':
        tag_list.append('wifi')
    if tags.get('smoking') == 'yes':
        tag_list.append('smoking_area')
    if tags.get('delivery') == 'yes':
        tag_list.append('delivery')
    if tags.get('takeaway') == 'yes':
        tag_list.append('takeaway')
    if tags.get('wheelchair') == 'yes':
        tag_list.append('wheelchair_accessible')
    
    return tag_list
