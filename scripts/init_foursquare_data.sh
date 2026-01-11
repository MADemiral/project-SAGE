#!/bin/bash
# Initial Foursquare data population script
# Runs once on container startup to populate restaurants and entertainment venues

set -e

echo "======================================"
echo "Foursquare Data Initialization"
echo "======================================"
date

# Wait for database to be ready
echo "Waiting for database to be ready..."
until python -c "import psycopg2; conn = psycopg2.connect(dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}', host='${POSTGRES_HOST}'); conn.close()" 2>/dev/null; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done
echo "✓ Database is ready"

# Wait for ChromaDB to be ready
echo "Waiting for ChromaDB to be ready..."
until python -c "import requests; requests.get('http://${CHROMA_HOST}:${CHROMA_PORT}/api/v1/heartbeat', timeout=2)" 2>/dev/null; do
    echo "Waiting for ChromaDB..."
    sleep 2
done
echo "✓ ChromaDB is ready"

# Function to populate places (dining + entertainment)
populate_places() {
    echo ""
    echo "======================================"
    echo "Populating Places from Foursquare..."
    echo "======================================"
    python /app/scripts/create_places_embeddings.py
    if [ $? -eq 0 ]; then
        echo "✓ Places populated successfully"
        return 0
    else
        echo "✗ Failed to populate places"
        return 1
    fi
}

# Function to populate events
populate_events() {
    echo ""
    echo "======================================"
    echo "Populating Events from Bubilet..."
    echo "======================================"
    python /app/scripts/create_event_embeddings.py
    if [ $? -eq 0 ]; then
        echo "✓ Events populated successfully"
        return 0
    else
        echo "✗ Failed to populate events"
        return 1
    fi
}

# Run initial population
echo ""
echo "======================================"
echo "Starting Initial Data Population"
echo "======================================"

populate_places
populate_events

echo ""
echo "======================================"
echo "Initial Data Population Complete!"
echo "======================================"
date
