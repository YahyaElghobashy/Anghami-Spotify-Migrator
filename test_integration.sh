#!/bin/bash

# 🧪 Integration Test Script for Anghami → Spotify Migration Tool
# This script starts both backend and frontend for testing the complete system

set -e

echo "🧪 Starting Integration Test for Anghami → Spotify Migration Tool"
echo "=================================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is available
port_available() {
    ! lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1
}

# Function to wait for a service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e "${GREEN}✅ $name is ready!${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts - waiting for $name..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $name failed to start after $max_attempts attempts${NC}"
    return 1
}

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ npm found: $(npm --version)${NC}"

echo ""

# Check ports
echo "🔍 Checking port availability..."
if ! port_available 8000; then
    echo -e "${RED}❌ Port 8000 is already in use (needed for backend)${NC}"
    echo "   Please stop any service using port 8000 and try again"
    exit 1
fi
echo -e "${GREEN}✅ Port 8000 is available${NC}"

if ! port_available 3000; then
    echo -e "${RED}❌ Port 3000 is already in use (needed for frontend)${NC}"
    echo "   Please stop any service using port 3000 and try again"
    exit 1
fi
echo -e "${GREEN}✅ Port 3000 is available${NC}"

echo ""

# Install backend dependencies
echo "📦 Installing backend dependencies..."
if [ ! -f "backend_requirements.txt" ]; then
    echo -e "${RED}❌ backend_requirements.txt not found${NC}"
    exit 1
fi

pip3 install -r backend_requirements.txt >/dev/null 2>&1 || {
    echo -e "${RED}❌ Failed to install backend dependencies${NC}"
    exit 1
}
echo -e "${GREEN}✅ Backend dependencies installed${NC}"

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
if [ ! -d "ui" ]; then
    echo -e "${RED}❌ UI directory not found${NC}"
    exit 1
fi

cd ui
if [ ! -f "package.json" ]; then
    echo -e "${RED}❌ package.json not found in ui directory${NC}"
    exit 1
fi

npm install >/dev/null 2>&1 || {
    echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
    exit 1
}
echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating frontend .env file..."
    cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_ANALYTICS=false
EOF
    echo -e "${GREEN}✅ Frontend .env file created${NC}"
fi

cd ..

echo ""
echo "🚀 Starting services..."

# Start backend in background
echo "🔧 Starting backend API server..."
python3 backend_api.py > backend.log 2>&1 &
BACKEND_PID=$!
echo -e "${BLUE}📡 Backend API started (PID: $BACKEND_PID)${NC}"

# Wait for backend to be ready
if ! wait_for_service "http://localhost:8000/health" "Backend API"; then
    echo -e "${RED}❌ Backend failed to start. Check backend.log for details${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend in background
echo "🎨 Starting frontend UI server..."
cd ui
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${BLUE}🌐 Frontend UI started (PID: $FRONTEND_PID)${NC}"
cd ..

# Wait for frontend to be ready
if ! wait_for_service "http://localhost:3000" "Frontend UI"; then
    echo -e "${RED}❌ Frontend failed to start. Check frontend.log for details${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Integration test environment is ready!${NC}"
echo ""
echo "📱 Access the application:"
echo -e "   ${BLUE}Frontend UI:${NC} http://localhost:3000"
echo -e "   ${BLUE}Backend API:${NC} http://localhost:8000"
echo -e "   ${BLUE}API Docs:${NC} http://localhost:8000/docs"
echo ""
echo "🧪 Test the complete flow:"
echo "   1. Open http://localhost:3000 in your browser"
echo "   2. Click 'Connect with Spotify' (simulated auth)"
echo "   3. Select playlists to migrate"
echo "   4. Start migration and watch real-time progress"
echo "   5. See completion statistics"
echo ""
echo "📊 Monitor logs:"
echo "   Backend: tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both services${NC}"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Services stopped${NC}"
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Wait for user to stop
while true; do
    sleep 1
done 