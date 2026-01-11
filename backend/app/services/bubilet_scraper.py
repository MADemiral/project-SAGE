"""
Service for scraping events from bubilet.com.tr/ankara
Parses JSON data embedded in the HTML
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
import logging
from datetime import datetime
import re
import json

logger = logging.getLogger(__name__)

BUBILET_ANKARA_URL = "https://www.bubilet.com.tr/ankara"
BUBILET_BASE_URL = "https://www.bubilet.com.tr"


def scrape_ankara_events() -> List[Dict[str, Any]]:
    """
    Scrape events from bubilet.com.tr/ankara
    Parses JSON data embedded in the page
    
    Returns:
        List of event dictionaries with scraped data
    """
    try:
        logger.info("Starting to scrape events from bubilet.com.tr/ankara...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(BUBILET_ANKARA_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        html_content = response.text
        
        # Parse JSON data embedded in the HTML
        events = parse_json_events(html_content)
        
        if not events:
            logger.warning("No events found in JSON data, trying fallback scraper")
            # Fallback to HTML parsing if JSON parsing fails
            events = parse_html_events(html_content)
        
        logger.info(f"Successfully scraped {len(events)} events from bubilet")
        return events
        
    except Exception as e:
        logger.error(f"Error scraping bubilet: {e}")
        return []


def parse_json_events(html_content: str) -> List[Dict[str, Any]]:
    """
    Parse events from JSON data embedded in the HTML
    Bubilet uses Next.js which embeds data in script tags
    """
    events = []
    
    try:
        # The events data is in script tags with pattern: self.__next_f.push([1,"..."])
        # We need to extract and parse this JSON data
        
        # Find all script content that contains event data
        script_pattern = r'self\.__next_f\.push\(\[1,"(.*?)"\]\)'
        matches = re.findall(script_pattern, html_content)
        
        if not matches:
            logger.warning("No JSON data found in script tags")
            return []
        
        # Combine all JSON fragments
        combined_text = ""
        for match in matches:
            # Unescape the JSON string
            unescaped = match.replace('\\"', '"').replace('\\\\', '\\')
            combined_text += unescaped
        
        # Extract event objects - they have a consistent structure
        # Looking for: {"id":number, "name":"...", "slug":"...", "dates":[...], "price":..., "venues":[...]}
        event_pattern = r'\{"id":(\d+),"name":"([^"]+)","slug":"([^"]+)","dates":\[([^\]]+)\].*?"price":([\d.]+|null).*?"venues":\[\{"id":\d+,"name":"([^"]+)".*?"cityName":"Ankara"'
        
        event_matches = re.findall(event_pattern, combined_text)
        
        logger.info(f"Found {len(event_matches)} event matches in JSON data")
        
        for match in event_matches:
            event_id, name, slug, dates_str, price_str, venue = match
            
            # Parse the first date from dates array
            date_matches = re.findall(r'"([\d-]+T[\d:+]+)"', dates_str)
            event_date = None
            if date_matches:
                try:
                    # Parse ISO format date
                    date_str = date_matches[0].replace('+03:00', '+03:00').replace('+00:00', '+00:00')
                    event_date = datetime.fromisoformat(date_str)
                except Exception as e:
                    logger.debug(f"Error parsing date {date_matches[0]}: {e}")
            
            # Parse price
            try:
                price = float(price_str) if price_str != 'null' else 0.0
            except:
                price = 0.0
            
            # Build event URL - bubilet events are at /ankara/etkinlik/{slug}
            # The slug format needs the full path
            if slug.startswith('http'):
                event_url = slug
            elif slug.startswith('/'):
                event_url = f"{BUBILET_BASE_URL}{slug}"
            else:
                # Standard format: /ankara/etkinlik/{slug}
                event_url = f"{BUBILET_BASE_URL}/ankara/etkinlik/{slug}"
            
            # Determine category from name
            category = 'other'
            name_lower = name.lower()
            if 'konser' in name_lower or 'concert' in name_lower:
                category = 'music'
            elif 'tiyatro' in name_lower or 'oyun' in name_lower or 'theater' in name_lower:
                category = 'theater'
            elif 'workshop' in name_lower or 'atölye' in name_lower:
                category = 'workshop'
            elif 'stand-up' in name_lower or 'komedi' in name_lower:
                category = 'comedy'
            
            events.append({
                'title': name,
                'venue_name': venue,
                'event_date': event_date,
                'price_info': f"{price} TL" if price > 0 else 'Ücretsiz',
                'price': price,
                'event_url': event_url,
                'external_id': event_id,
                'source': 'bubilet',
                'venue_address': f"{venue}, Ankara",
                'is_active': True,
                'category': category,
                'description': f"{name} - {venue}"
            })
        
        # Remove duplicates based on event_id
        unique_events = {event['external_id']: event for event in events}
        events = list(unique_events.values())
        
        logger.info(f"Parsed {len(events)} unique events from JSON data")
        return events
        
    except Exception as e:
        logger.error(f"Error parsing JSON events: {e}")
        return []


def parse_html_events(html_content: str) -> List[Dict[str, Any]]:
    """
    Fallback parser using BeautifulSoup if JSON parsing fails
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        events = []
        
        # Try to find event containers
        event_containers = (
            soup.find_all('article') or
            soup.find_all('div', class_=re.compile(r'event|card|item', re.I)) or
            soup.find_all('a', href=re.compile(r'/ankara/|/etkinlik/', re.I))
        )
        
        logger.info(f"Found {len(event_containers)} potential event containers in HTML")
        
        for container in event_containers[:50]:  # Limit to first 50
            try:
                # Extract title
                title_elem = container.find(['h1', 'h2', 'h3', 'h4'])
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Extract link
                link = None
                if container.name == 'a':
                    link = container.get('href')
                else:
                    link_elem = container.find('a', href=True)
                    if link_elem:
                        link = link_elem['href']
                
                if not link:
                    continue
                
                # Make absolute URL
                if not link.startswith('http'):
                    link = f"{BUBILET_BASE_URL}{link}"
                
                # Extract venue if possible
                venue_elem = container.find(class_=re.compile(r'venue|location', re.I))
                venue = venue_elem.get_text(strip=True) if venue_elem else "Ankara"
                
                events.append({
                    'title': title,
                    'venue_name': venue,
                    'event_date': None,
                    'price_info': 'Bilet bilgisi için siteyi ziyaret edin',
                    'price': 0.0,
                    'event_url': link,
                    'external_id': link.split('/')[-1],
                    'source': 'bubilet',
                    'venue_address': f"{venue}, Ankara",
                    'is_active': True,
                    'category': 'event',
                    'description': title
                })
            except Exception as e:
                logger.debug(f"Error parsing container: {e}")
                continue
        
        # Remove duplicates
        unique_events = {event['event_url']: event for event in events}
        events = list(unique_events.values())
        
        logger.info(f"Parsed {len(events)} events from HTML fallback")
        return events
        
    except Exception as e:
        logger.error(f"Error parsing HTML events: {e}")
        return []


def parse_date_string(date_str: str) -> datetime:
    """
    Parse various date formats from Turkish websites
    """
    if not date_str:
        return None
    
    try:
        # Try ISO format first
        if 'T' in date_str or '-' in date_str:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        pass
    
    # Turkish month names mapping
    turkish_months = {
        'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
        'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
        'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
    }
    
    date_str_lower = date_str.lower()
    
    # Try to extract day, month, year
    for month_name, month_num in turkish_months.items():
        if month_name in date_str_lower:
            # Extract numbers
            numbers = re.findall(r'\d+', date_str)
            if numbers:
                day = int(numbers[0]) if len(numbers) > 0 else 1
                year = int(numbers[1]) if len(numbers) > 1 else datetime.now().year
                
                # Ensure year is 4 digits
                if year < 100:
                    year += 2000
                
                try:
                    return datetime(year, month_num, day)
                except ValueError:
                    pass
    
    # If all parsing fails, return None
    return None


def scrape_event_details(event_url: str) -> Dict[str, Any]:
    """
    Scrape detailed information from a single event page
    
    Args:
        event_url: URL of the event page
        
    Returns:
        Dictionary with detailed event information
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(event_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        details = {}
        
        # Extract detailed description
        desc_elem = soup.find('div', class_=re.compile(r'description|about|detail', re.I))
        if desc_elem:
            details['description'] = desc_elem.get_text(strip=True)
        
        # Extract more venue details
        venue_elem = soup.find(class_=re.compile(r'venue-address|location-detail', re.I))
        if venue_elem:
            details['venue_address'] = venue_elem.get_text(strip=True)
        
        # Extract multiple dates if it's a recurring event
        date_elems = soup.find_all(class_=re.compile(r'event-date|show-date', re.I))
        if date_elems:
            details['all_dates'] = [elem.get_text(strip=True) for elem in date_elems]
        
        return details
        
    except Exception as e:
        logger.error(f"Error scraping event details from {event_url}: {e}")
        return {}
