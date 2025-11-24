#!/bin/bash

# MNEE Nexus - Hardhat Mainnet Fork Startup Script
# This script starts a local Hardhat node forked from Ethereum mainnet
# with the real MNEE contract (0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF)

set -e

echo "🍴 Starting MNEE Nexus Hardhat Fork..."
echo ""

cd "$(dirname "$0")/../contracts"

# Check if .env exists, if not create a default one
if [ ! -f .env ]; then
    echo "⚠️  No .env file found in contracts/"
    echo "Creating .env with public RPC..."
    echo "ETH_MAINNET_RPC_URL=https://eth.llamarpc.com" > .env
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

echo "🚀 Starting Hardhat node with mainnet fork..."
echo "   Using RPC from .env"
echo ""
echo "📍 MNEE Contract: 0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF"
echo "🔗 RPC: http://127.0.0.1:8545"
echo "⛓️  Chain ID: 31337"
echo ""
echo "⏳ This will take a moment to sync the fork..."
echo ""

# Start Hardhat node (will keep running)
npx hardhat node