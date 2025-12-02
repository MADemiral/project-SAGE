#!/bin/bash
# Monthly course update script - runs scraper and updates embeddings

set -e

echo "=================================================="
echo "SAGE Monthly Course Update - $(date)"
echo "=================================================="

# Wait for services to be ready
echo "1. Checking if PostgreSQL and ChromaDB are ready..."
for i in {1..10}; do
    if pg_isready -h postgres -p 5432 -U sage_user > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    echo "   Waiting for PostgreSQL... ($i/10)"
    sleep 2
done

# Run scraper
echo ""
echo "2. Running course scraper to fetch latest data..."
cd /workspace/scraper && python scrape_multi_semester.py

# Check if scraping was successful
if [ $? -eq 0 ]; then
    echo "✓ Scraping completed successfully"
else
    echo "✗ Scraping failed"
    exit 1
fi

# Wait a bit
sleep 3

# Update embeddings (with 86% similarity deduplication)
echo ""
echo "3. Updating embeddings (checking for changes with 86% similarity threshold)..."
cd /workspace && python backend/scripts/create_course_embeddings.py

# Check if embedding update was successful
if [ $? -eq 0 ]; then
    echo "✓ Embeddings updated successfully"
else
    echo "✗ Embedding update failed"
    exit 1
fi

echo ""
echo "=================================================="
echo "✓ Monthly course update complete! - $(date)"
echo "=================================================="
