#!/usr/bin/env python3
"""
Test script to fetch venues from Foursquare API and save to JSON
"""
import sys
import os
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.foursquare_service import fetch_restaurants_from_foursquare, fetch_entertainment_from_foursquare
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Test Foursquare API and save results"""
    
    # Fetch dining venues
    logger.info("Fetching dining venues from Foursquare...")
    restaurants = fetch_restaurants_from_foursquare(limit=50)
    
    if restaurants:
        logger.info(f"✅ Found {len(restaurants)} dining venues")
        
        # Save to file
        output_file = 'foursquare_dining_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(restaurants, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {output_file}")
        
        # Print sample
        logger.info("\n=== Sample dining venues ===")
        for i, venue in enumerate(restaurants[:5], 1):
            logger.info(f"\n{i}. {venue['name']}")
            logger.info(f"   Category: {venue['category']}")
            logger.info(f"   Distance: {venue['distance_from_campus']} km")
            logger.info(f"   Address: {venue.get('address', 'N/A')}")
            if venue.get('rating'):
                logger.info(f"   Rating: {venue['rating']}")
            if venue.get('price'):
                logger.info(f"   Price: {'$' * venue['price']}")
    else:
        logger.error("❌ No dining venues found")
    
    # Fetch entertainment venues
    logger.info("\n" + "="*50)
    logger.info("Fetching entertainment venues from Foursquare...")
    entertainment = fetch_entertainment_from_foursquare(limit=50)
    
    if entertainment:
        logger.info(f"✅ Found {len(entertainment)} entertainment venues")
        
        # Save to file
        output_file = 'foursquare_entertainment_output.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(entertainment, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {output_file}")
        
        # Print sample
        logger.info("\n=== Sample entertainment venues ===")
        for i, venue in enumerate(entertainment[:5], 1):
            logger.info(f"\n{i}. {venue['name']}")
            logger.info(f"   Category: {venue['category']}")
            logger.info(f"   Distance: {venue['distance_from_campus']} km")
            logger.info(f"   Address: {venue.get('address', 'N/A')}")
    else:
        logger.error("❌ No entertainment venues found")


if __name__ == "__main__":
    main()
