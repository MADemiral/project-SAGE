#!/usr/bin/env python3
"""
Script to scrape events from bubilet.com and store them in PostgreSQL and ChromaDB
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
from app.services.bubilet_scraper import scrape_ankara_events
import logging
from datetime import datetime

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


def create_event_text(event: dict) -> str:
    """Create a text representation of an event for embedding"""
    parts = []
    
    # Title and type
    parts.append(f"Event: {event['title']}")
    if event.get('event_type'):
        parts.append(f"Type: {event['event_type']}")
    
    # Date and time
    if event.get('event_date'):
        if isinstance(event['event_date'], datetime):
            date_str = event['event_date'].strftime('%d %B %Y')
        else:
            date_str = str(event['event_date'])
        parts.append(f"Date: {date_str}")
    
    # Venue
    if event.get('venue_name'):
        parts.append(f"Venue: {event['venue_name']}")
    if event.get('venue_address'):
        parts.append(f"Location: {event['venue_address']}")
    
    # Description
    if event.get('description'):
        parts.append(f"Description: {event['description']}")
    
    # Price
    if event.get('price_info'):
        parts.append(f"Price: {event['price_info']}")
    
    return '\n'.join(parts)


def store_in_postgres(events: list):
    """Store events in PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Insert or update events - table already exists from init.sql
        inserted = 0
        updated = 0
        for event in events:
            try:
                # Check if exists
                cur.execute("SELECT id FROM events WHERE external_id = %s AND source = %s", 
                           (event.get('external_id'), event.get('source', 'bubilet')))
                exists = cur.fetchone()
                
                cur.execute("""
                    INSERT INTO events (
                        title, description, venue_name, venue_address,
                        event_date, end_date, price, price_info, category,
                        image_url, ticket_url, external_id, source, is_active
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (external_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        venue_name = EXCLUDED.venue_name,
                        venue_address = EXCLUDED.venue_address,
                        event_date = EXCLUDED.event_date,
                        end_date = EXCLUDED.end_date,
                        price = EXCLUDED.price,
                        price_info = EXCLUDED.price_info,
                        category = EXCLUDED.category,
                        image_url = EXCLUDED.image_url,
                        ticket_url = EXCLUDED.ticket_url,
                        updated_at = CURRENT_TIMESTAMP
                """, (
                    event['title'],
                    event.get('description'),
                    event.get('venue_name'),
                    event.get('venue_address'),
                    event.get('event_date'),
                    event.get('end_date'),
                    event.get('price', 0),
                    event.get('price_info'),
                    event.get('category', 'other'),
                    event.get('image_url'),
                    event.get('event_url'),  # ticket_url is the event URL
                    event.get('external_id'),
                    event.get('source', 'bubilet'),
                    event.get('is_active', True)
                ))
                
                if exists:
                    updated += 1
                else:
                    inserted += 1
                
            except Exception as e:
                logger.error(f"Error inserting event {event.get('title', 'Unknown')}: {e}")
                logger.error(f"Event data: {event}")
                continue
        
        conn.commit()
        logger.info(f"Stored {inserted} new and updated {updated} existing events in PostgreSQL")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error connecting to PostgreSQL: {e}")
        raise


def store_in_chromadb(events: list, model: SentenceTransformer):
    """Store event embeddings in ChromaDB"""
    try:
        # Connect to ChromaDB
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Get or create collection
        try:
            collection = client.get_collection("events")
            # Delete existing collection to refresh
            client.delete_collection("events")
        except:
            pass
        
        collection = client.create_collection(
            name="events",
            metadata={"description": "Event embeddings for social assistant"}
        )
        
        logger.info("Generating embeddings for events...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        embeddings = []
        metadatas = []
        
        for idx, event in enumerate(events):
            if not event.get('title'):
                continue
                
            # Create text representation
            text = create_event_text(event)
            
            # Add E5 passage prefix
            text_with_prefix = f"passage: {text}"
            
            # Generate embedding
            embedding = model.encode(text_with_prefix, convert_to_numpy=True)
            
            # Prepare metadata (ChromaDB doesn't accept None values)
            metadata = {
                'title': str(event.get('title', ''))[:500],  # Truncate if too long
                'event_type': str(event.get('event_type', ''))[:100],
                'venue_name': str(event.get('venue_name', ''))[:255],
                'venue_address': str(event.get('venue_address', ''))[:500],
                'ticket_url': str(event.get('event_url', ''))[:1000],  # Changed from event_url to ticket_url
                'price': str(event.get('price', ''))[:50],  # Numeric price (e.g., "2200")
                'price_info': str(event.get('price_info', ''))[:255],  # Price with currency (e.g., "2200.0 TL")
                'source': str(event.get('source', 'bubilet'))
            }
            
            # Add date if available
            if event.get('event_date'):
                if isinstance(event['event_date'], datetime):
                    metadata['event_date'] = event['event_date'].isoformat()
                else:
                    metadata['event_date'] = str(event['event_date'])
            else:
                metadata['event_date'] = ''
            
            ids.append(f"event_{idx}")
            documents.append(text)
            embeddings.append(embedding.tolist())
            metadatas.append(metadata)
        
        # Add to ChromaDB
        if ids:
            collection.add(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Stored {len(ids)} event embeddings in ChromaDB")
        else:
            logger.warning("No events to store in ChromaDB")
        
    except Exception as e:
        logger.error(f"Error storing in ChromaDB: {e}")
        raise


def main():
    """Main function to scrape and store event data"""
    try:
        # Load embedding model
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        model = SentenceTransformer(MODEL_NAME)
        
        # Try to load from test file first, otherwise scrape
        import json
        test_file = '/app/bubilet_test_output.json'
        events = None
        
        if os.path.exists(test_file):
            logger.info(f"Loading events from test file: {test_file}")
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    events = data.get('events', [])
                    logger.info(f"Loaded {len(events)} events from test file")
            except Exception as e:
                logger.warning(f"Could not load test file: {e}")
        
        # If no test file, scrape from website
        if not events:
            logger.info("Scraping events from bubilet.com.tr/ankara...")
            events = scrape_ankara_events()
        
        if not events:
            logger.warning("No events found!")
            return
        
        logger.info(f"Found {len(events)} events")
        
        # Store in PostgreSQL
        logger.info("Storing events in PostgreSQL...")
        store_in_postgres(events)
        
        # Store in ChromaDB
        logger.info("Storing event embeddings in ChromaDB...")
        store_in_chromadb(events, model)
        
        logger.info("✅ Successfully stored all event data!")
        
        # Print statistics
        event_types = {}
        for e in events:
            etype = e.get('event_type', 'Unknown')
            event_types[etype] = event_types.get(etype, 0) + 1
        
        logger.info("\n=== Statistics ===")
        logger.info(f"Total events: {len(events)}")
        logger.info(f"Event types: {len(event_types)}")
        for etype, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {etype}: {count}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise


if __name__ == "__main__":
    main()
