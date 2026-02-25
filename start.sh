#!/bin/bash
# GhostPen - Start Everything
# Usage: bash start.sh

echo "=== Starting GhostPen ==="

# Kill any old processes
echo "Cleaning up old processes..."
pkill -f "uvicorn server:app" 2>/dev/null
pkill -f "next-server" 2>/dev/null
rm -f /home/alexandratitus767/gptoss-alexandra-project/ghostpen/.next/dev/lock 2>/dev/null
sleep 1

# Load env vars
source /home/alexandratitus767/gptoss-alexandra-project/.env

# Start backend
echo "Starting backend on port 8001..."
cd /home/alexandratitus767/gptoss-alexandra-project/social-content-engine
source venv/bin/activate
python server.py > /tmp/ghostpen-backend.log 2>&1 &
BACKEND_PID=$!
echo "  Backend PID: $BACKEND_PID"

# Start frontend
echo "Starting frontend on port 3000..."
cd /home/alexandratitus767/gptoss-alexandra-project/ghostpen
npm run dev > /tmp/ghostpen-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "  Frontend PID: $FRONTEND_PID"

# Wait for servers to be ready
sleep 3

# Load GPT-OSS model into memory (in background)
echo "Loading GPT-OSS 120B into memory (this takes ~1-2 min)..."
ollama run gpt-oss:120b --keepalive 24h "ready" > /dev/null 2>&1 &

echo ""
echo "=== GhostPen is starting up ==="
echo ""
echo "  Frontend:  http://192.168.1.187:3000"
echo "  Backend:   http://192.168.1.187:8001"
echo ""
echo "  Backend log:  tail -f /tmp/ghostpen-backend.log"
echo "  Frontend log: tail -f /tmp/ghostpen-frontend.log"
echo ""
echo "  To stop everything:  bash stop.sh"
echo ""

# Keep script running so you can see it's alive
wait
