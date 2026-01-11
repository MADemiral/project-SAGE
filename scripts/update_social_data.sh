#!/bin/bash
# Periodic update script for social data
# Updates events daily and restaurants every 10 days

set -e

echo "======================================"
echo "Social Data Periodic Update"
echo "======================================"
date

# Function to update events
update_events() {
    echo ""
    echo "======================================"
    echo "Updating Events..."
    echo "======================================"
    python /app/scripts/create_event_embeddings.py
    if [ $? -eq 0 ]; then
        echo "✓ Events updated successfully"
    else
        echo "✗ Failed to update events"
    fi
}

# Function to update places (dining + entertainment)
update_places() {
    echo ""
    echo "======================================"
    echo "Updating Places..."
    echo "======================================"
    python /app/scripts/create_places_embeddings.py
    if [ $? -eq 0 ]; then
        echo "✓ Places updated successfully"
    else
        echo "✗ Failed to update places"
    fi
}

# Main loop
day_counter=0

while true; do
    echo ""
    echo "======================================"
    echo "Day $day_counter - Starting update cycle"
    echo "======================================"
    
    # Update events daily
    update_events
    
    # Update places every 10 days
    if [ $((day_counter % 10)) -eq 0 ]; then
        update_places
    fi
    
    day_counter=$((day_counter + 1))
    
    echo ""
    echo "======================================"
    echo "Next update in 24 hours..."
    echo "======================================"
    
    # Sleep for 24 hours
    sleep 86400
done
