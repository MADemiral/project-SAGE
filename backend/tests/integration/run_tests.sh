#!/bin/bash
# Quick setup script for running integration tests

echo "🚀 SAGE Integration Tests Setup"
echo "================================"

# Check if frontend and backend are running
echo ""
echo "📋 Pre-flight checks..."

# Check if port 5173 is in use (frontend)
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Frontend is running on port 5173"
else
    echo "❌ Frontend is NOT running on port 5173"
    echo "   Start it with: cd frontend && npm run dev"
fi

# Check if port 8000 is in use (backend)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend is NOT running on port 8000"
    echo "   Start it with: cd backend && uvicorn app.main:app --reload"
fi

# Check if Chrome/Chromium is installed
if command -v google-chrome &> /dev/null || command -v chromium-browser &> /dev/null; then
    echo "✅ Chrome/Chromium is installed"
else
    echo "⚠️  Chrome/Chromium not found - tests may fail"
    echo "   Install with: sudo apt-get install chromium-browser"
fi

echo ""
echo "📦 Installing test dependencies..."
pip install -q selenium webdriver-manager pytest pytest-xdist pytest-html

echo ""
echo "🧪 Running Integration Tests"
echo "============================="
echo ""

# Run tests
cd backend
python -m pytest tests/integration/ -v --html=integration_report.html --self-contained-html

echo ""
echo "✅ Tests complete! Check integration_report.html for detailed results."
