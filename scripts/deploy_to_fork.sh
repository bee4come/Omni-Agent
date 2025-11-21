#!/bin/bash

# Deploy contracts and setup MNEE on the running fork

set -e

echo "📜 Deploying contracts to Hardhat Fork..."
echo ""

cd "$(dirname "$0")/../contracts"

# Check if fork is running
if ! curl -s http://127.0.0.1:8545 > /dev/null 2>&1; then
    echo "❌ Error: Hardhat fork is not running!"
    echo ""
    echo "Please start the fork first:"
    echo "   ./scripts/start_fork.sh"
    echo ""
    echo "Then in another terminal, run this script again."
    exit 1
fi

echo "✅ Fork is running"
echo ""

# Run setup script
echo "🔧 Running setup script..."
echo ""
npx hardhat run scripts/setup_fork.ts --network localhost

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Copy the contract addresses from above"
echo "2. Update backend/.env with the addresses"
echo "3. Start the backend: cd backend && uvicorn app.main:app --reload"
echo "4. Start the frontend: cd frontend && npm run dev"
echo ""
