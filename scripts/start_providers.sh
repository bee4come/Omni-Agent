#!/bin/bash

# Start all provider services in the background
# MNEE Nexus / Omni-Agent Provider Services

echo "=========================================="
echo "Starting MNEE Provider Services"
echo "=========================================="

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Kill any existing provider processes
echo "Stopping existing provider services..."
pkill -f "providers/imagegen/main.py" 2>/dev/null
pkill -f "providers/price_oracle/main.py" 2>/dev/null
pkill -f "providers/batch_compute/main.py" 2>/dev/null
pkill -f "providers/log_archive/main.py" 2>/dev/null
sleep 2

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start ImageGen Provider (port 8001)
echo "Starting ImageGen Provider on port 8001..."
cd "$PROJECT_ROOT/providers/imagegen"
python main.py > "$PROJECT_ROOT/logs/imagegen.log" 2>&1 &
echo $! > "$PROJECT_ROOT/logs/imagegen.pid"

# Start PriceOracle Provider (port 8002)
echo "Starting PriceOracle Provider on port 8002..."
cd "$PROJECT_ROOT/providers/price_oracle"
python main.py > "$PROJECT_ROOT/logs/price_oracle.log" 2>&1 &
echo $! > "$PROJECT_ROOT/logs/price_oracle.pid"

# Start BatchCompute Provider (port 8003)
echo "Starting BatchCompute Provider on port 8003..."
cd "$PROJECT_ROOT/providers/batch_compute"
python main.py > "$PROJECT_ROOT/logs/batch_compute.log" 2>&1 &
echo $! > "$PROJECT_ROOT/logs/batch_compute.pid"

# Start LogArchive Provider (port 8004)
echo "Starting LogArchive Provider on port 8004..."
cd "$PROJECT_ROOT/providers/log_archive"
python main.py > "$PROJECT_ROOT/logs/log_archive.log" 2>&1 &
echo $! > "$PROJECT_ROOT/logs/log_archive.pid"

echo ""
echo "=========================================="
echo "All providers started!"
echo "=========================================="
echo "ImageGen:     http://localhost:8001"
echo "PriceOracle:  http://localhost:8002"
echo "BatchCompute: http://localhost:8003"
echo "LogArchive:   http://localhost:8004"
echo ""
echo "Logs are in: $PROJECT_ROOT/logs/"
echo "=========================================="

sleep 2

# Check if all services are running
echo ""
echo "Checking service health..."
curl -s http://localhost:8001/health >/dev/null && echo "✓ ImageGen is healthy" || echo "✗ ImageGen failed to start"
curl -s http://localhost:8002/health >/dev/null && echo "✓ PriceOracle is healthy" || echo "✗ PriceOracle failed to start"
curl -s http://localhost:8003/health >/dev/null && echo "✓ BatchCompute is healthy" || echo "✗ BatchCompute failed to start"
curl -s http://localhost:8004/health >/dev/null && echo "✓ LogArchive is healthy" || echo "✗ LogArchive failed to start"
echo ""
