#!/usr/bin/env python3
"""
Script to verify social assistant data in PostgreSQL and ChromaDB
"""

import psycopg2
import chromadb
from datetime import datetime
import os

# Database connection
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'postgres'),
    'port': os.getenv('POSTGRES_PORT', 5432),
    'database': os.getenv('POSTGRES_DB', 'sage_db'),
    'user': os.getenv('POSTGRES_USER', 'sage_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'sage_password')
}

# ChromaDB connection
CHROMA_HOST = os.getenv('CHROMA_HOST', 'chromadb')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', 8000))

def check_postgres():
    """Check PostgreSQL tables"""
    print("\n" + "="*60)
    print("PostgreSQL Database Check")
    print("="*60)
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Check restaurants table
        cursor.execute("SELECT COUNT(*) FROM restaurants")
        restaurant_count = cursor.fetchone()[0]
        print(f"\n✓ Restaurants table: {restaurant_count} records")
        
        if restaurant_count > 0:
            # Get some sample data
            cursor.execute("""
                SELECT name, cuisine_type, distance_from_campus 
                FROM restaurants 
                ORDER BY distance_from_campus 
                LIMIT 5
            """)
            print("\n  Top 5 nearest restaurants:")
            for row in cursor.fetchall():
                name, cuisine, distance = row
                print(f"    • {name} ({cuisine}) - {distance:.2f} km")
            
            # Get cuisine statistics
            cursor.execute("""
                SELECT cuisine_type, COUNT(*) as count 
                FROM restaurants 
                WHERE cuisine_type IS NOT NULL
                GROUP BY cuisine_type 
                ORDER BY count DESC 
                LIMIT 5
            """)
            print("\n  Top 5 cuisines:")
            for row in cursor.fetchall():
                cuisine, count = row
                print(f"    • {cuisine}: {count} restaurants")
        
        # Check events table
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        print(f"\n✓ Events table: {event_count} records")
        
        if event_count > 0:
            # Get upcoming events
            cursor.execute("""
                SELECT title, venue_name, event_date, category 
                FROM events 
                WHERE event_date >= CURRENT_DATE 
                ORDER BY event_date 
                LIMIT 5
            """)
            print("\n  Upcoming events:")
            for row in cursor.fetchall():
                title, venue, date, category = row
                date_str = date.strftime('%Y-%m-%d') if date else 'TBA'
                print(f"    • {title} at {venue} ({date_str}) - {category}")
            
            # Get category statistics
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM events 
                WHERE category IS NOT NULL
                GROUP BY category 
                ORDER BY count DESC
            """)
            print("\n  Event categories:")
            for row in cursor.fetchall():
                category, count = row
                print(f"    • {category}: {count} events")
        
        cursor.close()
        conn.close()
        
        return restaurant_count, event_count
        
    except Exception as e:
        print(f"\n✗ Error connecting to PostgreSQL: {e}")
        return 0, 0


def check_chromadb():
    """Check ChromaDB collections"""
    print("\n" + "="*60)
    print("ChromaDB Vector Store Check")
    print("="*60)
    
    try:
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        
        # Check restaurants collection
        try:
            restaurants_collection = client.get_collection("tedu_restaurants")
            restaurant_count = restaurants_collection.count()
            print(f"\n✓ tedu_restaurants collection: {restaurant_count} embeddings")
        except Exception as e:
            print(f"\n✗ tedu_restaurants collection not found: {e}")
            restaurant_count = 0
        
        # Check events collection
        try:
            events_collection = client.get_collection("tedu_events")
            event_count = events_collection.count()
            print(f"✓ tedu_events collection: {event_count} embeddings")
        except Exception as e:
            print(f"✗ tedu_events collection not found: {e}")
            event_count = 0
        
        return restaurant_count, event_count
        
    except Exception as e:
        print(f"\n✗ Error connecting to ChromaDB: {e}")
        return 0, 0


def main():
    print("\n" + "="*60)
    print("Social Assistant Data Verification")
    print("="*60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check PostgreSQL
    pg_restaurants, pg_events = check_postgres()
    
    # Check ChromaDB
    chroma_restaurants, chroma_events = check_chromadb()
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"\nPostgreSQL:")
    print(f"  • Restaurants: {pg_restaurants}")
    print(f"  • Events: {pg_events}")
    print(f"\nChromaDB:")
    print(f"  • Restaurant embeddings: {chroma_restaurants}")
    print(f"  • Event embeddings: {chroma_events}")
    
    # Status
    print("\n" + "="*60)
    if pg_restaurants > 0 and pg_events > 0 and chroma_restaurants > 0 and chroma_events > 0:
        print("✓ Social Assistant is FULLY OPERATIONAL!")
        print("="*60)
        print("\nYou can now test in the UI:")
        print("  1. Open: http://localhost")
        print("  2. Go to Social Assistant tab")
        print("  3. Ask questions like:")
        print("     - 'yakındaki türk restoranları' (nearby turkish restaurants)")
        print("     - 'bu hafta konser var mı?' (are there concerts this week?)")
        print("     - 'italian restaurant öner' (recommend italian restaurant)")
    else:
        print("⚠ Data incomplete. Run: ./scripts/init_social_data.sh")
        print("="*60)
    print()


if __name__ == "__main__":
    main()
