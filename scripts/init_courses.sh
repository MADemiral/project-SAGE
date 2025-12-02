#!/bin/bash
# Initialize course data: scrape courses and create embeddings

set -e

echo "=================================================="
echo "SAGE Course Data Initialization"
echo "=================================================="

# Wait for services to be ready
echo "1. Waiting for PostgreSQL and ChromaDB to be ready..."
for i in {1..30}; do
    if pg_isready -h postgres -p 5432 -U sage_user > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    echo "   Waiting for PostgreSQL... ($i/30)"
    sleep 2
done

sleep 5

# Run scraper
echo ""
echo "2. Running course scraper..."
cd /workspace/scraper && python scrape_multi_semester.py

# Check if scraping was successful
if [ $? -eq 0 ]; then
    echo "✓ Scraping completed successfully"
else
    echo "✗ Scraping failed"
    exit 1
fi

# Wait a bit
sleep 5

# Create embeddings
echo ""
echo "3. Creating embeddings and storing in ChromaDB + PostgreSQL..."
cd /workspace && python backend/scripts/create_course_embeddings.py

# Check if embedding creation was successful
if [ $? -eq 0 ]; then
    echo "✓ Embeddings created successfully"
else
    echo "✗ Embedding creation failed"
    exit 1
fi

echo ""
echo "=================================================="
echo "✓ Course data initialization complete!"
echo "=================================================="

