#!/bin/bash

# Resume Critic AI - Full Stack Startup Script
# This script starts both the backend and frontend servers

echo "🚀 Starting Resume Critic AI..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use. Please stop the process using port $1 and try again."
        exit 1
    fi
}

# Check if required ports are available
echo "🔍 Checking port availability..."
check_port 8001  # Backend
check_port 3000  # Frontend

# Function to cleanup background processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    pkill -f "uvicorn main:app" 2>/dev/null
    pkill -f "next dev" 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend server
echo "🔧 Starting backend server on port 8001..."
cd backend
uvicorn main:app --host 127.0.0.1 --port 8001 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Check if backend started successfully
if ! curl -s http://localhost:8001/api/health > /dev/null; then
    echo "❌ Backend failed to start. Check the logs above for errors."
    cleanup
fi

echo "✅ Backend server started successfully!"

# Start frontend server
echo "🎨 Starting frontend server on port 3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

echo ""
echo "🎉 Resume Critic AI is now running!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8001"
echo "📊 Health Check: http://localhost:8001/api/health"
echo ""
echo "Press Ctrl+C to stop all servers"
echo ""

# Wait for user to stop the servers
wait 