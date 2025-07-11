#!/bin/bash

# ResumeWise - AI-Powered Agentic Resume Analyzer
# Start script for dual-system architecture

set -e

echo "Starting ResumeWise - AI-Powered Agentic Resume Analyzer"
echo "======================================================"

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "Port $1 is already in use"
        return 1
    fi
    return 0
}

echo ""
echo "Checking Prerequisites..."

# Check Python
if ! command_exists python3; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check Node.js
if ! command_exists node; then
    echo "Error: Node.js is required but not installed"
    exit 1
fi

# Check npm
if ! command_exists npm; then
    echo "Error: npm is required but not installed"
    exit 1
fi

echo "Prerequisites check passed"

# Check ports
echo ""
echo "Checking port availability..."
if ! check_port 8000; then
    echo "Error: Backend port 8000 is already in use. Please stop the existing process or use a different port."
    exit 1
fi

if ! check_port 3000; then
    echo "Error: Frontend port 3000 is already in use. Please stop the existing process or use a different port."
    exit 1
fi

echo "Ports 3000 and 8000 are available"

# Setup Backend
echo ""
echo "Setting up Backend (Python/FastAPI)..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check environment variables
echo "Checking environment variables..."
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Creating template..."
    cat > .env << EOF
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Judgment Labs Configuration  
JUDGMENT_API_KEY=your_judgment_api_key_here
JUDGMENT_ORG_ID=your_judgment_org_id_here

# Optional: Monitoring Configuration
JUDGMENT_MONITORING=true
JUDGMENT_EVALUATIONS=true
EOF
    echo "Please edit backend/.env with your API keys before running the server"
    echo "   - Get OpenAI API key from: https://platform.openai.com/api-keys"
    echo "   - Get Judgment API key from: https://judgmentlabs.ai"
fi

# Start backend in background
echo "Starting Backend Server (Port 8000)..."
echo "   Dual-System Architecture:"
echo "   - Primary Scoring: Fast agent decisions (< 1 second)" 
echo "   - Judgment Framework: Comprehensive evaluation (2-5 seconds)"
echo ""

python -m uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 --log-level info --no-access-log &
BACKEND_PID=$!

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Test backend health
if curl -s http://localhost:8000/health > /dev/null; then
    echo "Backend is running successfully"
    echo "   - API Documentation: http://localhost:8000/docs"
    echo "   - Health Check: http://localhost:8000/health"
else
    echo "Error: Backend failed to start properly"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Setup Frontend
echo ""
echo "Setting up Frontend (Next.js)..."
cd ../frontend

echo "Installing Node.js dependencies..."
npm install

# Start frontend in background  
echo "Starting Frontend Server (Port 3000)..."
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to start
echo "Waiting for frontend to initialize..."
sleep 8

# Test frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "Frontend is running successfully"
else
    echo "Error: Frontend failed to start properly"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi

# Success message
echo ""
echo "ResumeWise is now running!"
echo "======================================================"
echo ""
echo "Frontend Application: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Judgment Dashboard: https://judgmentlabs.ai"
echo ""
echo "Monitor your agent traces at: https://judgmentlabs.ai/traces"
echo "View evaluations at: https://judgmentlabs.ai/evaluations"
echo ""
echo "Features Active:"
echo "   - Fast primary scoring for real-time decisions"
echo "   - Comprehensive Judgment evaluation in parallel"
echo "   - Complete observability and tracing"
echo "   - Pattern detection and monitoring"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
trap 'echo ""; echo "Stopping servers..."; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo "Servers stopped successfully"; exit 0' INT

# Keep the script running
wait 