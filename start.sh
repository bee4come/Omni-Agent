#!/bin/bash

# Kill existing processes on ports
fuser -k 8000/tcp 8001/tcp 8002/tcp 8003/tcp 8004/tcp 3000/tcp

# Start Providers
echo "Starting Providers..."
python3 providers/imagegen/main.py > providers_imagegen.log 2>&1 &
python3 providers/price_oracle/main.py > providers_price.log 2>&1 &
python3 providers/batch_compute/main.py > providers_batch.log 2>&1 &
python3 providers/log_archive/main.py > providers_log.log 2>&1 &

# Start Backend
echo "Starting Backend..."
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
cd ..

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
cd ..

echo "All services started!"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
