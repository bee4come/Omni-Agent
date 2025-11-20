#!/bin/bash

# Quick health check for MNEE Nexus Backend

echo "🏥 MNEE Nexus Backend Health Check"
echo "===================================="
echo ""

# Check if server is running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend server is running"
    
    # Get basic info
    echo ""
    echo "📊 Server Info:"
    curl -s http://localhost:8000/ | python3 -m json.tool
    
    echo ""
    echo "📈 Quick Stats:"
    curl -s http://localhost:8000/stats | python3 -m json.tool
    
    echo ""
    echo "💰 Treasury Status:"
    curl -s http://localhost:8000/treasury | python3 -m json.tool | head -20
    
    echo ""
    echo "✅ All systems operational!"
    echo "📖 Visit http://localhost:8000/docs for API documentation"
else
    echo "❌ Backend server is NOT running"
    echo ""
    echo "To start the backend:"
    echo "  cd backend && ./start_backend.sh"
    exit 1
fi
