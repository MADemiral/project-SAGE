#!/usr/bin/env python3
"""
Script to fetch restaurants from Foursquare API and store them in PostgreSQL and ChromaDB
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extras import execute_values
import chromadb
from sentence_transformers import SentenceTransformer
import numpy as np
from app.services.foursquare_service import fetch_restaurants_from_foursquare, TED_UNIVERSITY_LAT, TED_UNIVERSITY_LON
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'sage_db'),
    'user': os.getenv('POSTGRES_USER', 'sage_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'sage_password'),
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

# ChromaDB configuration
CHROMA_HOST = os.getenv('CHROMA_HOST', 'chromadb')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', '8000'))

# Embedding model
MODEL_NAME = "intfloat/e5-large-v2"


def create_restaurant_text(restaurant: dict) -> str:
    """Create a text representation of a restaurant for embedding"""
    parts = []
    
    # Name and category
    parts.append(f"Restaurant: {restaurant['name']}")
    if restaurant.get('category'):
        parts.append(f"Type: {restaurant['category']}")
    
    # Categories from Foursquare
    if restaurant.get('categories'):
        categories_str = ', '.join(restaurant['categories'])
        parts.append(f"Categories: {categories_str}")
    
    # Location and distance
    parts.append(f"Distance from TED University: {restaurant['distance_from_campus']:.2f} km")
    if restaurant.get('address'):
        parts.append(f"Address: {restaurant['address']}")
    
    # Features and tags
    if restaurant.get('tags'):
        tags_str = ', '.join(restaurant['tags'])
        parts.append(f"Features: {tags_str}")
    
    # Description
    if restaurant.get('description'):
        parts.append(f"Description: {restaurant['description']}")
    
    # Rating and price
    if restaurant.get('rating'):
        parts.append(f"Rating: {restaurant['rating']}")
    
    if restaurant.get('price'):
        parts.append(f"Price level: {restaurant['price']}")
    
    # Opening hours
    if restaurant.get('opening_hours'):
        if isinstance(restaurant['opening_hours'], dict):
            hours = restaurant['opening_hours'].get('display', '')
            if hours:
                parts.append(f"Opening hours: {hours}")
        else:
            parts.append(f"Opening hours: {restaurant['opening_hours']}")
    
    # Contact
    if restaurant.get('phone'):
        parts.append(f"Phone: {restaurant['phone']}")
    
    if restaurant.get('website'):
        parts.append(f"Website: {restaurant['website']}")
    
    return '\n'.join(parts)


def store_in_postgres(restaurants: list):
    """Store restaurants in PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Insert or update restaurants - table already exists from init.sql
        inserted = 0
        updated = 0
        for restaurant in restaurants:
            try:
                # Prepare amenities as JSONB
                amenities = {}
                if restaurant.get('tags'):
                    amenities['tags'] = restaurant['tags']
                if restaurant.get('opening_hours'):
                    amenities['opening_hours'] = restaurant['opening_hours']
                if restaurant.get('photos'):
                    amenities['photos'] = restaurant['photos']
                
                # Check if exists (using fsq_id)
                unique_id = restaurant.get('fsq_id')
                if not unique_id:
                    logger.warning(f"Skipping restaurant {restaurant['name']} - no fsq_id")
                    continue
                    
                cur.execute("SELECT id FROM restaurants WHERE fsq_id = %s", (unique_id,))
                exists = cur.fetchone()
                
                # Get first category as cuisine type
                cuisine = None
                if restaurant.get('categories') and len(restaurant['categories']) > 0:
                    cuisine = restaurant['categories'][0]
                
                cur.execute("""
                    INSERT INTO restaurants (
                        name, cuisine_type, category, address, latitude, longitude,
                        phone, website, opening_hours, price_range, rating,
                        distance_from_campus, tags, amenities, fsq_id, source
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (fsq_id) DO UPDATE SET
                        name = EXCLUDED.name,
                        cuisine_type = EXCLUDED.cuisine_type,
                        category = EXCLUDED.category,
                        address = EXCLUDED.address,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        phone = EXCLUDED.phone,
                        website = EXCLUDED.website,
                        opening_hours = EXCLUDED.opening_hours,
                        price_range = EXCLUDED.price_range,
                        rating = EXCLUDED.rating,
                        tags = EXCLUDED.tags,
                        amenities = EXCLUDED.amenities,
                        distance_from_campus = EXCLUDED.distance_from_campus,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    restaurant['name'],
                    cuisine,
                    restaurant.get('category'),
                    restaurant.get('address'),
                    restaurant['latitude'],
                    restaurant['longitude'],
                    restaurant.get('phone'),
                    restaurant.get('website'),
                    str(restaurant.get('opening_hours')) if restaurant.get('opening_hours') else None,
                    restaurant.get('price'),  # Foursquare uses 'price' (integer tier)
                    restaurant.get('rating'),
                    restaurant['distance_from_campus'],
                    psycopg2.extras.Json(restaurant.get('tags', [])),
                    psycopg2.extras.Json(amenities),
                    unique_id,
                    'foursquare'
                ))
                
                if exists:
                    updated += 1
                else:
                    inserted += 1
                
            except Exception as e:
                logger.error(f"Error inserting restaurant {restaurant['name']}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Stored {inserted} new and updated {updated} existing restaurants in PostgreSQL")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise


def store_in_chromadb(restaurants: list, model: SentenceTransformer):
    """Store restaurant embeddings in ChromaDB"""
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Get or create collection
        try:
            collection = client.get_collection("restaurants")
            # Delete existing collection to refresh
            client.delete_collection("restaurants")
        except:
            pass
        
        collection = client.create_collection(
            name="restaurants",
            metadata={"description": "Restaurant embeddings for social assistant"}
        )
        
        logger.info("Generating embeddings for restaurants...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for idx, restaurant in enumerate(restaurants):
            # Create text representation
            text = create_restaurant_text(restaurant)
            
            # Add E5 query prefix for better retrieval
            text_with_prefix = f"passage: {text}"
            
            # Generate embedding
            embedding = model.encode(text_with_prefix, convert_to_numpy=True)
            
            # Prepare metadata (ChromaDB doesn't accept None values)
            metadata = {
                'name': str(restaurant['name']),
                'category': str(restaurant.get('category') or ''),
                'cuisine_type': str(restaurant.get('categories', [None])[0] or ''),  # First category as cuisine
                'address': str(restaurant.get('address') or ''),
                'latitude': float(restaurant['latitude']),
                'longitude': float(restaurant['longitude']),
                'distance_from_campus': float(restaurant['distance_from_campus']),
                'fsq_id': str(restaurant.get('fsq_id') or restaurant.get('osm_id') or ''),
                'tags': ','.join(restaurant.get('tags', [])),
                'phone': str(restaurant.get('phone') or ''),
                'website': str(restaurant.get('website') or ''),
                'rating': str(restaurant.get('rating') or ''),
                'price': str(restaurant.get('price') or '')
            }
            
            ids.append(f"restaurant_{idx}")
            documents.append(text)
            embeddings.append(embedding.tolist())
            metadatas.append(metadata)
        
        # Add to ChromaDB
        collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        logger.info(f"Stored {len(restaurants)} restaurant embeddings in ChromaDB")
        
    except Exception as e:
        logger.error(f"Error storing in ChromaDB: {e}")
        raise


def main():
    """Main function to fetch and store restaurant data"""
    try:
        # Load embedding model
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        # Try to load from test file first, otherwise fetch from API
        import json
        test_file = '/app/foursquare_test_output.json'
        restaurants = None
        
        if os.path.exists(test_file):
            logger.info(f"Loading restaurants from test file: {test_file}")
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both list and dict formats
                    if isinstance(data, list):
                        restaurants = data
                    else:
                        restaurants = data.get('restaurants', [])
                    logger.info(f"Loaded {len(restaurants)} restaurants from test file")
            except Exception as e:
                logger.warning(f"Could not load test file: {e}")
        
        # If no test file, fetch from API
        if not restaurants:
            logger.info("Fetching restaurants from Foursquare API (limit: 50)...")
            restaurants = fetch_restaurants_from_foursquare(limit=50)
        
        if not restaurants:
            logger.warning("No restaurants found!")
            return
        
        logger.info(f"Found {len(restaurants)} restaurants")
        
        # Store in PostgreSQL
        logger.info("Storing restaurants in PostgreSQL...")
        store_in_postgres(restaurants)
        
        # Store in ChromaDB
        logger.info("Storing restaurant embeddings in ChromaDB...")
        store_in_chromadb(restaurants, model)
        
        logger.info("✅ Successfully stored all restaurant data!")
        
        # Print statistics
        cuisine_types = {}
        for r in restaurants:
            cuisine = r.get('cuisine_type', 'Unknown')
            cuisine_types[cuisine] = cuisine_types.get(cuisine, 0) + 1
        
        logger.info("\n=== Statistics ===")
        logger.info(f"Total restaurants: {len(restaurants)}")
        logger.info(f"Cuisine types: {len(cuisine_types)}")
        for cuisine, count in sorted(cuisine_types.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  - {cuisine}: {count}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
