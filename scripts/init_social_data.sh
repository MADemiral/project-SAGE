#!/bin/bash

# Script to initialize social assistant data
# Populates restaurants and events into PostgreSQL and ChromaDB

set -e  # Exit on error

echo "=========================================="
echo "Social Assistant Data Initialization"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${BLUE}Installing required packages...${NC}"
pip install -q -r backend/requirements.txt

# Check if PostgreSQL is running
echo -e "${BLUE}Checking PostgreSQL connection...${NC}"
if docker ps | grep -q sage_postgres; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not running. Starting services...${NC}"
    docker-compose up -d postgres chromadb
    echo "Waiting for PostgreSQL to be ready..."
    sleep 10
fi

# Check if ChromaDB is running
if docker ps | grep -q sage_chromadb; then
    echo -e "${GREEN}✓ ChromaDB is running${NC}"
else
    echo -e "${RED}✗ ChromaDB is not running. Starting it...${NC}"
    docker-compose up -d chromadb
    echo "Waiting for ChromaDB to be ready..."
    sleep 5
fi

echo ""
echo "=========================================="
echo "Step 1: Populating Restaurants"
echo "=========================================="
echo -e "${BLUE}Fetching restaurants from OpenStreetMap (Ankara)...${NC}"
echo "This will fetch all restaurants in Ankara and create embeddings."
echo ""

cd backend
python scripts/create_restaurant_embeddings.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Restaurants populated successfully${NC}"
else
    echo -e "${RED}✗ Failed to populate restaurants${NC}"
    exit 1
fi

echo ""
echo "=========================================="
echo "Step 2: Populating Events"
echo "=========================================="
echo -e "${BLUE}Scraping events from Bubilet.com.tr (Ankara)...${NC}"
echo "This will scrape all events in Ankara and create embeddings."
echo ""

python scripts/create_event_embeddings.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Events populated successfully${NC}"
else
    echo -e "${RED}✗ Failed to populate events${NC}"
    exit 1
fi

cd ..

echo ""
echo "=========================================="
echo "Data Population Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  • Restaurants: Stored in PostgreSQL + ChromaDB (tedu_restaurants)"
echo "  • Events: Stored in PostgreSQL + ChromaDB (tedu_events)"
echo ""
echo -e "${GREEN}The social assistant is now ready to use!${NC}"
echo ""
echo "To test in UI:"
echo "  1. Start all services: docker-compose up -d"
echo "  2. Open: http://localhost"
echo "  3. Navigate to Social Assistant tab"
echo "  4. Try queries like:"
echo "     - 'yakındaki restoranlar' (nearby restaurants)"
echo "     - 'bu hafta hangi konserler var?' (concerts this week)"
echo "     - 'italian restaurant önerir misin?' (italian restaurant recommendations)"
echo ""
