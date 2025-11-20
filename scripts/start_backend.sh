#!/bin/bash

# Start MNEE Nexus Backend (FastAPI)

echo "=========================================="
echo "Starting MNEE Nexus Backend"
echo "=========================================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Kill any existing backend process
echo "Stopping existing backend..."
pkill -f "backend/app/main.py" 2>/dev/null
sleep 2

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Check if virtual environment exists
if [ ! -d "$PROJECT_ROOT/backend/venv" ]; then
    echo "Virtual environment not found. Creating..."
    cd "$PROJECT_ROOT/backend"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source "$PROJECT_ROOT/backend/venv/bin/activate"
fi

# Start backend API
echo "Starting MNEE Nexus Backend API on port 8000..."
cd "$PROJECT_ROOT/backend"
export PYTHONPATH="$PROJECT_ROOT/backend:$PYTHONPATH"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
echo $! > "$PROJECT_ROOT/logs/backend.pid"

echo ""
echo "=========================================="
echo "Backend API started!"
echo "=========================================="
echo "API Docs:  http://localhost:8000/docs"
echo "API:       http://localhost:8000"
echo ""
echo "Log file:  $PROJECT_ROOT/logs/backend.log"
echo "=========================================="

sleep 3

# Check if service is running
echo ""
echo "Checking backend health..."
curl -s http://localhost:8000/ >/dev/null && echo "✓ Backend is healthy" || echo "✗ Backend failed to start (check logs)"
echo ""
