#!/bin/bash

##############################################################################
# MNEE Nexus / Omni-Agent - Master Startup Script
#
# This script orchestrates the startup of the entire system:
# 1. Local Ethereum node (Hardhat)
# 2. Deploy smart contracts
# 3. Start 4 service providers
# 4. Start backend API
#
# Usage:
#   ./start_all.sh          # Start all services
#   ./start_all.sh stop     # Stop all services
#   ./start_all.sh restart  # Restart all services
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log files directory
LOG_DIR="$(pwd)/logs"
mkdir -p "$LOG_DIR"

# PID files directory
PID_DIR="$(pwd)/pids"
mkdir -p "$PID_DIR"

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "${BLUE}"
    echo "===================================================================="
    echo "  $1"
    echo "===================================================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    print_info "Waiting for $name to be ready..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            print_success "$name is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    print_error "$name failed to start within timeout"
    return 1
}

##############################################################################
# Service Management
##############################################################################

start_hardhat() {
    print_header "Starting Hardhat Node"
    
    cd contracts
    
    if [ -f "$PID_DIR/hardhat.pid" ]; then
        print_warning "Hardhat may already be running. Stopping first..."
        stop_hardhat
    fi
    
    npx hardhat node > "$LOG_DIR/hardhat.log" 2>&1 &
    echo $! > "$PID_DIR/hardhat.pid"
    
    cd ..
    
    wait_for_service "http://localhost:8545" "Hardhat"
    print_success "Hardhat node started (PID: $(cat $PID_DIR/hardhat.pid))"
}

stop_hardhat() {
    if [ -f "$PID_DIR/hardhat.pid" ]; then
        local pid=$(cat "$PID_DIR/hardhat.pid")
        print_info "Stopping Hardhat (PID: $pid)..."
        kill $pid 2>/dev/null || true
        rm "$PID_DIR/hardhat.pid"
        print_success "Hardhat stopped"
    fi
}

deploy_contracts() {
    print_header "Deploying Smart Contracts"
    
    cd contracts
    npx hardhat run scripts/deploy.js --network localhost
    cd ..
    
    # Update backend .env with deployment addresses
    if [ -f "contracts/deployments.json" ]; then
        print_info "Updating backend configuration with contract addresses..."
        # This would parse deployments.json and update backend/.env
        # For now, we'll print instructions
        print_warning "Please manually update backend/.env with the contract addresses from contracts/deployments.json"
    fi
    
    print_success "Contracts deployed successfully"
}

start_providers() {
    print_header "Starting Service Providers"
    
    # ImageGen Provider (Port 8001)
    print_info "Starting ImageGen Provider..."
    cd providers/imagegen
    python3 main.py > "$LOG_DIR/imagegen.log" 2>&1 &
    echo $! > "$PID_DIR/imagegen.pid"
    cd ../..
    
    # PriceOracle Provider (Port 8002)
    print_info "Starting PriceOracle Provider..."
    cd providers/price_oracle
    python3 main.py > "$LOG_DIR/priceoracle.log" 2>&1 &
    echo $! > "$PID_DIR/priceoracle.pid"
    cd ../..
    
    # BatchCompute Provider (Port 8003)
    print_info "Starting BatchCompute Provider..."
    cd providers/batch_compute
    python3 main.py > "$LOG_DIR/batchcompute.log" 2>&1 &
    echo $! > "$PID_DIR/batchcompute.pid"
    cd ../..
    
    # LogArchive Provider (Port 8004)
    print_info "Starting LogArchive Provider..."
    cd providers/log_archive
    python3 main.py > "$LOG_DIR/logarchive.log" 2>&1 &
    echo $! > "$PID_DIR/logarchive.pid"
    cd ../..
    
    # Wait for all providers to be ready
    wait_for_service "http://localhost:8001/docs" "ImageGen"
    wait_for_service "http://localhost:8002/docs" "PriceOracle"
    wait_for_service "http://localhost:8003/docs" "BatchCompute"
    wait_for_service "http://localhost:8004/docs" "LogArchive"
    
    print_success "All service providers started"
}

stop_providers() {
    print_info "Stopping service providers..."

    for provider in imagegen priceoracle batchcompute logarchive; do
        if [ -f "$PID_DIR/$provider.pid" ]; then
            local pid=$(cat "$PID_DIR/$provider.pid")
            kill $pid 2>/dev/null || true
            rm "$PID_DIR/$provider.pid"
        fi
    done

    print_success "Service providers stopped"
}

start_guardian() {
    print_header "Starting Guardian Service"

    cd backend

    if [ -f "$PID_DIR/guardian.pid" ]; then
        print_warning "Guardian may already be running. Stopping first..."
        stop_guardian
    fi

    print_info "Starting Guardian Service (Port 8100)..."
    python3 -m guardian.service > "$LOG_DIR/guardian.log" 2>&1 &
    echo $! > "$PID_DIR/guardian.pid"

    cd ..

    wait_for_service "http://localhost:8100/" "Guardian Service"
    print_success "Guardian Service started (PID: $(cat $PID_DIR/guardian.pid))"
}

stop_guardian() {
    if [ -f "$PID_DIR/guardian.pid" ]; then
        local pid=$(cat "$PID_DIR/guardian.pid")
        print_info "Stopping Guardian (PID: $pid)..."
        kill $pid 2>/dev/null || true
        rm "$PID_DIR/guardian.pid"
        print_success "Guardian stopped"
    fi
}

start_backend() {
    print_header "Starting Backend API"
    
    cd backend
    
    if [ -f "$PID_DIR/backend.pid" ]; then
        print_warning "Backend may already be running. Stopping first..."
        stop_backend
    fi
    
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
    echo $! > "$PID_DIR/backend.pid"
    
    cd ..
    
    wait_for_service "http://localhost:8000/" "Backend API"
    print_success "Backend API started (PID: $(cat $PID_DIR/backend.pid))"
}

stop_backend() {
    if [ -f "$PID_DIR/backend.pid" ]; then
        local pid=$(cat "$PID_DIR/backend.pid")
        print_info "Stopping Backend (PID: $pid)..."
        kill $pid 2>/dev/null || true
        rm "$PID_DIR/backend.pid"
        print_success "Backend stopped"
    fi
}

##############################################################################
# Main Commands
##############################################################################

start_all() {
    print_header "Starting MNEE Nexus / Omni-Agent"
    
    # Check prerequisites
    check_command node
    check_command npx
    check_command python3
    check_command curl
    
    # Start services in order
    start_hardhat
    sleep 5
    deploy_contracts
    sleep 2
    start_providers
    sleep 2
    start_guardian
    sleep 2
    start_backend

    print_header "System Ready!"
    print_success "All services are running:"
    echo ""
    echo "  Hardhat Node:          http://localhost:8545"
    echo "  ImageGen Provider:     http://localhost:8001/docs"
    echo "  PriceOracle Provider:  http://localhost:8002/docs"
    echo "  BatchCompute Provider: http://localhost:8003/docs"
    echo "  LogArchive Provider:   http://localhost:8004/docs"
    echo "  Guardian Service:      http://localhost:8100/"
    echo "  Backend API:           http://localhost:8000/docs"
    echo ""
    echo "  Logs directory: $LOG_DIR/"
    echo "  PIDs directory: $PID_DIR/"
    echo ""
    print_info "Press Ctrl+C to stop all services, or run: ./start_all.sh stop"
}

stop_all() {
    print_header "Stopping MNEE Nexus / Omni-Agent"

    stop_backend
    stop_guardian
    stop_providers
    stop_hardhat

    print_success "All services stopped"
}

restart_all() {
    stop_all
    sleep 2
    start_all
}

show_status() {
    print_header "Service Status"
    
    check_service() {
        local name=$1
        local pid_file=$2
        local url=$3
        
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p $pid > /dev/null 2>&1; then
                if [ -n "$url" ] && curl -s "$url" > /dev/null 2>&1; then
                    print_success "$name: Running (PID: $pid) ✓"
                else
                    print_warning "$name: Process running but not responding (PID: $pid)"
                fi
            else
                print_error "$name: Not running (stale PID file)"
            fi
        else
            print_error "$name: Not running"
        fi
    }
    
    check_service "Hardhat" "$PID_DIR/hardhat.pid" "http://localhost:8545"
    check_service "ImageGen" "$PID_DIR/imagegen.pid" "http://localhost:8001/docs"
    check_service "PriceOracle" "$PID_DIR/priceoracle.pid" "http://localhost:8002/docs"
    check_service "BatchCompute" "$PID_DIR/batchcompute.pid" "http://localhost:8003/docs"
    check_service "LogArchive" "$PID_DIR/logarchive.pid" "http://localhost:8004/docs"
    check_service "Backend" "$PID_DIR/backend.pid" "http://localhost:8000/"
}

show_logs() {
    local service=$1
    
    if [ -z "$service" ]; then
        print_info "Available logs: hardhat, imagegen, priceoracle, batchcompute, logarchive, backend"
        print_info "Usage: ./start_all.sh logs <service>"
        return
    fi
    
    if [ -f "$LOG_DIR/$service.log" ]; then
        tail -f "$LOG_DIR/$service.log"
    else
        print_error "Log file not found: $LOG_DIR/$service.log"
    fi
}

##############################################################################
# Entry Point
##############################################################################

case "${1:-start}" in
    start)
        start_all
        ;;
    stop)
        stop_all
        ;;
    restart)
        restart_all
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs <service>}"
        exit 1
        ;;
esac
