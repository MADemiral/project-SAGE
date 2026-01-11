#!/usr/bin/env python3
"""
Script to fetch places (dining & entertainment) from Foursquare API and store them in PostgreSQL and ChromaDB
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
from app.services.foursquare_service import (
    fetch_venues_from_foursquare,
    CAMPUS_LAT, 
    CAMPUS_LON
)
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


def create_place_text(place: dict, venue_type: str) -> str:
    """Create a text representation of a place for embedding"""
    parts = []
    
    # Name and category
    parts.append(f"Place: {place['name']}")
    parts.append(f"Type: {venue_type}")
    
    if place.get('category'):
        parts.append(f"Category: {place['category']}")
    
    # Categories from Foursquare
    if place.get('categories'):
        categories_str = ', '.join(place['categories'])
        parts.append(f"Categories: {categories_str}")
    
    # Location and distance
    parts.append(f"Distance from TED University: {place['distance_from_campus']:.2f} km")
    if place.get('address'):
        parts.append(f"Address: {place['address']}")
    
    # Features and tags
    if place.get('tags'):
        tags_str = ', '.join(place['tags'])
        parts.append(f"Features: {tags_str}")
    
    # Description
    if place.get('description'):
        parts.append(f"Description: {place['description']}")
    
    # Rating and price
    if place.get('rating'):
        parts.append(f"Rating: {place['rating']}")
    
    if place.get('price'):
        parts.append(f"Price level: {place['price']}")
    
    # Opening hours
    if place.get('opening_hours'):
        if isinstance(place['opening_hours'], dict):
            hours = place['opening_hours'].get('display', '')
            if hours:
                parts.append(f"Opening hours: {hours}")
        else:
            parts.append(f"Opening hours: {place['opening_hours']}")
    
    # Contact
    if place.get('phone'):
        parts.append(f"Phone: {place['phone']}")
    
    if place.get('website'):
        parts.append(f"Website: {place['website']}")
    
    return '\n'.join(parts)


def store_in_postgres(places: list, venue_type: str):
    """Store places in PostgreSQL, aggregating categories for same fsq_id"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Group places by fsq_id and aggregate their categories
        places_by_id = {}
        for place in places:
            fsq_id = place.get('fsq_id')
            if not fsq_id:
                logger.warning(f"Skipping place {place['name']} - no fsq_id")
                continue
            
            category = place.get('category')
            if fsq_id not in places_by_id:
                places_by_id[fsq_id] = place.copy()
                places_by_id[fsq_id]['search_categories'] = [category]
            else:
                # Add this category to the list if not already there
                if category not in places_by_id[fsq_id]['search_categories']:
                    places_by_id[fsq_id]['search_categories'].append(category)
        
        # Insert or update places
        inserted = 0
        updated = 0
        for fsq_id, place in places_by_id.items():
            try:
                # Prepare amenities as JSONB
                amenities = {}
                if place.get('tags'):
                    amenities['tags'] = place['tags']
                if place.get('opening_hours'):
                    amenities['opening_hours'] = place['opening_hours']
                if place.get('photos'):
                    amenities['photos'] = place['photos']
                
                # Check if exists
                cur.execute("SELECT id, category FROM places WHERE fsq_id = %s", (fsq_id,))
                existing = cur.fetchone()
                
                # Get first category as cuisine type (for dining venues)
                cuisine = None
                if venue_type == 'dining' and place.get('categories') and len(place['categories']) > 0:
                    cuisine = place['categories'][0]
                
                if existing:
                    # Update existing place, merging categories
                    existing_id, existing_categories = existing
                    # Merge categories
                    merged_categories = list(set(existing_categories + place['search_categories']))
                    
                    cur.execute("""
                        UPDATE places SET
                            name = %s,
                            category = %s,
                            address = %s,
                            latitude = %s,
                            longitude = %s,
                            phone = %s,
                            website = %s,
                            opening_hours = %s,
                            price_range = %s,
                            rating = %s,
                            tags = %s,
                            amenities = %s,
                            distance_from_campus = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE fsq_id = %s
                    """, (
                        place['name'],
                        merged_categories,
                        place.get('address'),
                        place['latitude'],
                        place['longitude'],
                        place.get('phone'),
                        place.get('website'),
                        str(place.get('opening_hours')) if place.get('opening_hours') else None,
                        place.get('price'),
                        place.get('rating'),
                        place.get('tags', []),
                        psycopg2.extras.Json(amenities),
                        place['distance_from_campus'],
                        fsq_id
                    ))
                    updated += 1
                else:
                    # Insert new place
                    cur.execute("""
                        INSERT INTO places (
                            name, venue_type, cuisine_type, category, address, latitude, longitude,
                            phone, website, opening_hours, price_range, rating,
                            distance_from_campus, tags, amenities, fsq_id, source
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        place['name'],
                        venue_type,
                        cuisine,
                        place['search_categories'],  # Array of categories
                        place.get('address'),
                        place['latitude'],
                        place['longitude'],
                        place.get('phone'),
                        place.get('website'),
                        str(place.get('opening_hours')) if place.get('opening_hours') else None,
                        place.get('price'),
                        place.get('rating'),
                        place['distance_from_campus'],
                        place.get('tags', []),
                        psycopg2.extras.Json(amenities),
                        fsq_id,
                        'foursquare'
                    ))
                    inserted += 1
                
            except Exception as e:
                logger.error(f"Error inserting place {place['name']}: {e}")
                continue
        
        conn.commit()
        logger.info(f"Stored {inserted} new and updated {updated} existing {venue_type} places in PostgreSQL")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise


def store_in_chromadb(places: list, venue_type: str, model: SentenceTransformer):
    """Store place embeddings in ChromaDB - works with deduplicated places"""
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Collection name based on venue type
        collection_name = f"{venue_type}_places"
        
        # Get or create collection
        try:
            collection = client.get_collection(collection_name)
            # Delete existing collection to refresh
            client.delete_collection(collection_name)
        except:
            pass
        
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": f"{venue_type.capitalize()} place embeddings for social assistant"}
        )
        
        logger.info(f"Generating embeddings for {venue_type} places...")
        
        # Group places by fsq_id to deduplicate (same as PostgreSQL)
        places_by_id = {}
        for place in places:
            fsq_id = place.get('fsq_id')
            if not fsq_id:
                continue
            
            category = place.get('category')
            if fsq_id not in places_by_id:
                places_by_id[fsq_id] = place.copy()
                places_by_id[fsq_id]['search_categories'] = [category]
            else:
                # Add this category to the list if not already there
                if category not in places_by_id[fsq_id]['search_categories']:
                    places_by_id[fsq_id]['search_categories'].append(category)
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for idx, (fsq_id, place) in enumerate(places_by_id.items()):
            # Create text representation
            text = create_place_text(place, venue_type)
            
            # Add E5 query prefix for better retrieval
            text_with_prefix = f"passage: {text}"
            
            # Generate embedding
            embedding = model.encode(text_with_prefix, convert_to_numpy=True)
            
            # Prepare metadata (ChromaDB doesn't accept None values or arrays)
            metadata = {
                'name': str(place['name']),
                'venue_type': venue_type,
                'category': ','.join(place.get('search_categories', [])),  # Join array as comma-separated
                'cuisine_type': str(place.get('categories', [None])[0] or ''),
                'address': str(place.get('address') or ''),
                'latitude': float(place['latitude']),
                'longitude': float(place['longitude']),
                'distance_from_campus': float(place['distance_from_campus']),
                'fsq_id': str(fsq_id),
                'tags': ','.join(place.get('tags', [])),
                'phone': str(place.get('phone') or ''),
                'website': str(place.get('website') or ''),
                'rating': str(place.get('rating') or ''),
                'price': str(place.get('price') or '')
            }
            
            ids.append(f"{venue_type}_place_{idx}")
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
        
        logger.info(f"Stored {len(places_by_id)} unique {venue_type} place embeddings in ChromaDB")
        
    except Exception as e:
        logger.error(f"Error storing in ChromaDB: {e}")
        raise


def main():
    """Main function to fetch and store place data"""
    try:
        # Load embedding model
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        # === DINING VENUES ===
        logger.info("\n" + "="*60)
        logger.info("FETCHING DINING VENUES")
        logger.info("="*60)
        
        # Fetch dining venues from Foursquare API (50 per category)
        import json
        logger.info("Fetching dining venues from Foursquare API (50 per category)...")
        from app.services.foursquare_service import fetch_venues_from_foursquare
        dining_places = fetch_venues_from_foursquare(venue_type='dining', limit=50)
        
        if dining_places:
            logger.info(f"Found {len(dining_places)} dining venues")
            
            # Store in PostgreSQL
            logger.info("Storing dining places in PostgreSQL...")
            store_in_postgres(dining_places, 'dining')
            
            # Store in ChromaDB
            logger.info("Storing dining place embeddings in ChromaDB...")
            store_in_chromadb(dining_places, 'dining', model)
            
            logger.info("✅ Successfully stored all dining place data!")
        else:
            logger.warning("No dining places found!")
        
        # === ENTERTAINMENT VENUES ===
        logger.info("\n" + "="*60)
        logger.info("FETCHING ENTERTAINMENT VENUES")
        logger.info("="*60)
        
        # Fetch entertainment venues from Foursquare API (50 per category)
        logger.info("Fetching entertainment venues from Foursquare API (50 per category)...")
        entertainment_places = fetch_venues_from_foursquare(venue_type='entertainment', limit=50)
        
        if entertainment_places:
            logger.info(f"Found {len(entertainment_places)} entertainment venues")
            
            # Store in PostgreSQL
            logger.info("Storing entertainment places in PostgreSQL...")
            store_in_postgres(entertainment_places, 'entertainment')
            
            # Store in ChromaDB
            logger.info("Storing entertainment place embeddings in ChromaDB...")
            store_in_chromadb(entertainment_places, 'entertainment', model)
            
            logger.info("✅ Successfully stored all entertainment place data!")
        else:
            logger.warning("No entertainment places found!")
        
        # Print summary statistics
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Total dining venues: {len(dining_places) if dining_places else 0}")
        logger.info(f"Total entertainment venues: {len(entertainment_places) if entertainment_places else 0}")
        logger.info(f"Total places: {(len(dining_places) if dining_places else 0) + (len(entertainment_places) if entertainment_places else 0)}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
