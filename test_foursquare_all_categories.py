#!/usr/bin/env python3
"""
Test script to fetch venues from all 7 categories and save raw API responses
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
FSQ_API_KEY = os.getenv("FSQ_API_KEY", "X5FQEAYUXOZF3FC1LQN4Y2ED2YBHLYJP2W3LDYXIZJSCHRM5")
CAMPUS_LAT = 39.92424862995977
CAMPUS_LON = 32.861328748007665

# All 7 categories
CATEGORIES = {
    "restaurant": "4d4b7105d754a06374d81259",
    "cafe": "63be6904847c3692a84b9bb6",
    "dessert_shop": "4bf58dd8d48988d1d0941735",
    "cafeteria": "4bf58dd8d48988d128941735",
    "dining_drinking": "63be6904847c3692a84b9bb5",
    "arcade": "4bf58dd8d48988d1e1931735",
    "art_gallery": "4bf58dd8d48988d1e2931735",
}

def fetch_category(category_name, category_id, limit=50):
    """Fetch venues for a specific category"""
    print(f"\n{'='*60}")
    print(f"Fetching: {category_name} (ID: {category_id})")
    print(f"{'='*60}")
    
    params = {
        "ll": f"{CAMPUS_LAT},{CAMPUS_LON}",
        "fsq_category_ids": category_id,
        "limit": limit,
        "sort": "DISTANCE"
    }
    
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {FSQ_API_KEY}',
        'X-Places-Api-Version': '2025-06-17'
    }
    
    try:
        response = requests.get(
            "https://places-api.foursquare.com/places/search",
            params=params,
            headers=headers,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✓ Found {len(results)} venues")
            
            # Show first 5 venues
            print(f"\nFirst 5 venues:")
            for i, venue in enumerate(results[:5]):
                name = venue.get('name', 'Unknown')
                distance = venue.get('distance', 0)
                fsq_id = venue.get('fsq_place_id', 'N/A')
                categories = [cat.get('name') for cat in venue.get('categories', [])]
                print(f"  {i+1}. {name}")
                print(f"     Distance: {distance}m, FSQ ID: {fsq_id}")
                print(f"     Categories: {', '.join(categories)}")
            
            return {
                'category_name': category_name,
                'category_id': category_id,
                'total_results': len(results),
                'results': results
            }
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"Response: {response.text}")
            return {
                'category_name': category_name,
                'category_id': category_id,
                'error': response.text,
                'status_code': response.status_code
            }
            
    except Exception as e:
        print(f"✗ Exception: {e}")
        return {
            'category_name': category_name,
            'category_id': category_id,
            'error': str(e)
        }


def main():
    print("="*60)
    print("FOURSQUARE API TEST - ALL 7 CATEGORIES")
    print(f"Campus Location: {CAMPUS_LAT}, {CAMPUS_LON}")
    print(f"Limit: 50 venues per category")
    print("="*60)
    
    all_results = {}
    unique_fsq_ids = set()
    
    # Fetch from all categories
    for category_name, category_id in CATEGORIES.items():
        result = fetch_category(category_name, category_id, limit=50)
        all_results[category_name] = result
        
        # Track unique fsq_ids
        if 'results' in result:
            for venue in result['results']:
                fsq_id = venue.get('fsq_place_id')
                if fsq_id:
                    unique_fsq_ids.add(fsq_id)
    
    # Save to JSON file
    output_file = 'foursquare_all_categories_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    total_fetched = 0
    for category_name, result in all_results.items():
        count = result.get('total_results', 0)
        total_fetched += count
        print(f"{category_name:20s}: {count:3d} venues")
    
    print(f"\n{'='*60}")
    print(f"Total API results fetched: {total_fetched}")
    print(f"Unique venues (by fsq_id): {len(unique_fsq_ids)}")
    print(f"Average duplicates per venue: {total_fetched / len(unique_fsq_ids) if unique_fsq_ids else 0:.1f}")
    print(f"\n✓ Results saved to: {output_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
