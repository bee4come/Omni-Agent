#!/bin/bash

# MNEE Guardian Service Startup Script

set -e

echo "======================================================================"
echo "  Starting MNEE Guardian Service"
echo "======================================================================"

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "Error: .env file not found in backend/"
    echo "Please copy .env.example to .env and configure it"
    exit 1
fi

# Check if TREASURY_PRIVATE_KEY is set
source ../.env
if [ -z "$TREASURY_PRIVATE_KEY" ]; then
    echo "Error: TREASURY_PRIVATE_KEY not set in .env"
    exit 1
fi

# Set default port if not specified
export GUARDIAN_PORT=${GUARDIAN_PORT:-8100}

echo "Configuration:"
echo "  Port: $GUARDIAN_PORT"
echo "  Environment: ${MNEE_ENV:-local}"
echo "======================================================================"

# Start Guardian Service
cd ..
python -m guardian.service

