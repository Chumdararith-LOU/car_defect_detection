#!/bin/bash

echo "🟢 Starting Car Defect Detection Platform..."
echo "Backend:  http://localhost:8010"
echo "Frontend: http://localhost:3000 (dev mode)"
echo "Production UI: http://localhost:8010 (if frontend is built)"
echo "Press Ctrl+C to stop both servers."
echo ""

# Start Backend in background
cd backend
uvicorn main:app --reload --port 8010 &
BACKEND_PID=$!
cd ..

# Start Frontend in background
cd frontend
bun run dev &
FRONTEND_PID=$!
cd ..

# Trap Ctrl+C to kill both processes cleanly
trap "echo '\n🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Wait for processes
wait
