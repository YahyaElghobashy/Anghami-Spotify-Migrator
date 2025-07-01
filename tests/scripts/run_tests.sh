#!/bin/bash

# Anghami-Spotify Migration Tool - Test Runner
# Comprehensive end-to-end testing with Playwright

set -e

# Get the absolute path to the project root (two directories up from this script)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BROWSER="chromium"
HEADLESS="false"
PROJECT=""
SPECIFIC_TEST=""
SETUP_ONLY="false"

# Function to display usage
show_usage() {
    echo -e "${BLUE}Anghami-Spotify Migration Tool - Test Runner${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -b, --browser BROWSER     Run tests on specific browser (chromium, firefox, webkit)"
    echo "  -p, --project PROJECT     Run specific project (chromium-desktop, mobile-chrome, etc.)"
    echo "  -t, --test TEST           Run specific test file or test name"
    echo "  -h, --headless           Run tests in headless mode"
    echo "  -s, --setup-only         Only run setup without tests"
    echo "  -d, --debug              Run tests in debug mode with UI"
    echo "  -r, --report             Open HTML test report after completion"
    echo "  --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Run all tests with default settings"
    echo "  $0 -b firefox -h                     # Run tests in Firefox headless"
    echo "  $0 -p mobile-chrome                  # Run mobile Chrome tests"
    echo "  $0 -t \"profile input\"               # Run specific test"
    echo "  $0 -d                                # Run in debug mode"
    echo "  $0 -s                                # Setup environment only"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT="$2"
            shift 2
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        -h|--headless)
            HEADLESS="true"
            shift
            ;;
        -s|--setup-only)
            SETUP_ONLY="true"
            shift
            ;;
        -d|--debug)
            HEADLESS="false"
            DEBUG_MODE="true"
            shift
            ;;
        -r|--report)
            OPEN_REPORT="true"
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed${NC}"
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm is not installed${NC}"
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to setup environment
setup_environment() {
    echo -e "${BLUE}🚀 Setting up test environment...${NC}"
    
    # Create necessary directories
    mkdir -p data/test-results
    mkdir -p data/screenshots
    mkdir -p data/logs
    
    # Install Playwright if not already installed
    if [ ! -d "node_modules/@playwright" ]; then
        echo -e "${YELLOW}📦 Installing Playwright...${NC}"
        npm install @playwright/test
        npx playwright install
    fi
    
    # Install frontend dependencies if needed
    if [ ! -d "ui/node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        cd ui && npm install && cd ..
    fi
    
    # Install backend dependencies if needed
    if [ ! -f "backend_requirements.txt" ] || [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 Setting up backend dependencies...${NC}"
        python -m pip install -r backend_requirements.txt 2>/dev/null || python3 -m pip install -r backend_requirements.txt
    fi
    
    echo -e "${GREEN}✅ Environment setup completed${NC}"
}

# Function to start services
start_services() {
    echo -e "${BLUE}🌐 Starting services...${NC}"
    
    # Start backend
    echo -e "${YELLOW}Starting backend server...${NC}"
    python backend_api.py &
    BACKEND_PID=$!
    sleep 3
    
    # Check if backend is running
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ Backend health check failed, continuing anyway...${NC}"
    else
        echo -e "${GREEN}✅ Backend server is running${NC}"
    fi
    
    # Start frontend
    echo -e "${YELLOW}Starting frontend server...${NC}"
    cd ui
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    sleep 5
    
    # Check if frontend is running
    if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️ Frontend health check failed, continuing anyway...${NC}"
    else
        echo -e "${GREEN}✅ Frontend server is running${NC}"
    fi
    
    # Store PIDs for cleanup
    echo $BACKEND_PID > data/logs/backend.pid
    echo $FRONTEND_PID > data/logs/frontend.pid
}

# Function to stop services
stop_services() {
    echo -e "${BLUE}🛑 Stopping services...${NC}"
    
    # Kill backend
    if [ -f "data/logs/backend.pid" ]; then
        BACKEND_PID=$(cat data/logs/backend.pid)
        kill $BACKEND_PID 2>/dev/null || true
        rm data/logs/backend.pid
    fi
    
    # Kill frontend
    if [ -f "data/logs/frontend.pid" ]; then
        FRONTEND_PID=$(cat data/logs/frontend.pid)
        kill $FRONTEND_PID 2>/dev/null || true
        rm data/logs/frontend.pid
    fi
    
    # Kill any remaining Node.js processes on our ports
    lsof -ti:5173 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
    
    echo -e "${GREEN}✅ Services stopped${NC}"
}

# Function to run tests
run_tests() {
    echo -e "${BLUE}🧪 Running tests...${NC}"
    
    # Build test command - use the config from tests/config directory
    TEST_CMD="npx playwright test --config=tests/config/playwright.config.js"
    
    # Add project filter
    if [ ! -z "$PROJECT" ]; then
        TEST_CMD="$TEST_CMD --project=$PROJECT"
    fi
    
    # Add specific test filter
    if [ ! -z "$SPECIFIC_TEST" ]; then
        TEST_CMD="$TEST_CMD --grep=\"$SPECIFIC_TEST\""
    fi
    
    # Add headless mode
    if [ "$HEADLESS" = "true" ]; then
        TEST_CMD="$TEST_CMD --headed=false"
    else
        TEST_CMD="$TEST_CMD --headed=true"
    fi
    
    # Add debug mode
    if [ "$DEBUG_MODE" = "true" ]; then
        TEST_CMD="$TEST_CMD --debug"
    fi
    
    # Run the tests
    echo -e "${YELLOW}Executing: $TEST_CMD${NC}"
    eval $TEST_CMD
    
    TEST_EXIT_CODE=$?
    
    if [ $TEST_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
    else
        echo -e "${RED}❌ Some tests failed (exit code: $TEST_EXIT_CODE)${NC}"
    fi
    
    return $TEST_EXIT_CODE
}

# Function to generate report
generate_report() {
    echo -e "${BLUE}📊 Generating test report...${NC}"
    
    # Generate HTML report
    npx playwright show-report data/test-results/html-report 2>/dev/null || true
    
    if [ "$OPEN_REPORT" = "true" ]; then
        echo -e "${YELLOW}Opening test report in browser...${NC}"
        if command -v open &> /dev/null; then
            open data/test-results/html-report/index.html
        elif command -v xdg-open &> /dev/null; then
            xdg-open data/test-results/html-report/index.html
        else
            echo -e "${YELLOW}Please open data/test-results/html-report/index.html in your browser${NC}"
        fi
    fi
    
    echo -e "${GREEN}✅ Report generated: data/test-results/html-report/index.html${NC}"
}

# Cleanup function
cleanup() {
    echo -e "${BLUE}🧹 Cleaning up...${NC}"
    stop_services
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Trap cleanup on exit
trap cleanup EXIT

# Main execution
main() {
    echo -e "${BLUE}🎵 Anghami-Spotify Migration Tool - Test Runner${NC}"
    echo "======================================================"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # If setup only, exit here
    if [ "$SETUP_ONLY" = "true" ]; then
        echo -e "${GREEN}✅ Setup completed. Services are ready for testing.${NC}"
        exit 0
    fi
    
    # Start services
    start_services
    
    # Wait a moment for services to fully start
    echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
    sleep 5
    
    # Run tests
    run_tests
    TEST_RESULT=$?
    
    # Generate report
    generate_report
    
    # Print summary
    echo ""
    echo "======================================================"
    if [ $TEST_RESULT -eq 0 ]; then
        echo -e "${GREEN}🎉 Test execution completed successfully!${NC}"
    else
        echo -e "${RED}❌ Test execution completed with failures${NC}"
    fi
    echo -e "${BLUE}📁 Test artifacts saved to: data/test-results/${NC}"
    echo -e "${BLUE}📸 Screenshots saved to: data/screenshots/${NC}"
    echo -e "${BLUE}📄 Logs saved to: data/logs/${NC}"
    echo "======================================================"
    
    exit $TEST_RESULT
}

# Run main function
main 