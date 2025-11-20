#!/bin/bash

# Stop all MNEE Nexus services

echo "=========================================="
echo "Stopping all MNEE Nexus services"
echo "=========================================="

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Stop processes from PID files
for service in backend imagegen price_oracle batch_compute log_archive; do
    if [ -f "$PROJECT_ROOT/logs/${service}.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/logs/${service}.pid")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping $service (PID: $PID)..."
            kill $PID
        fi
        rm "$PROJECT_ROOT/logs/${service}.pid"
    fi
done

# Fallback: kill by process name
pkill -f "backend/app/main.py" 2>/dev/null
pkill -f "providers/imagegen/main.py" 2>/dev/null
pkill -f "providers/price_oracle/main.py" 2>/dev/null
pkill -f "providers/batch_compute/main.py" 2>/dev/null
pkill -f "providers/log_archive/main.py" 2>/dev/null

echo ""
echo "=========================================="
echo "All services stopped"
echo "=========================================="
