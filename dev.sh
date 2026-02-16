#!/bin/bash

# Kill background processes on exit
trap 'kill $(jobs -p)' EXIT

echo "Starting The Last Dialogue locally..."

# Start Backend
echo "Starting Backend on port 8000..."
(
    cd backend
    if [ ! -d "venv" ]; then
        echo "Creating venv..."
        python3 -m venv venv
    fi
    source venv/bin/activate
    pip install -r requirements.txt
    uvicorn server:app --reload --host 0.0.0.0 --port 8000
) &
BACKEND_PID=$!

# Start Frontend
echo "Starting Frontend on port 3000..."
(
    cd frontend
    if [ ! -d "node_modules" ]; then
        npm install
    fi
    npm run dev
) &
FRONTEND_PID=$!

wait $BACKEND_PID $FRONTEND_PID
