#!/bin/bash

# YourCast Development Startup Script
echo "🚀 Starting YourCast development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

echo -e "${BLUE}Checking prerequisites...${NC}"

# Check PostgreSQL connectivity
echo -e "${BLUE}Checking PostgreSQL connection...${NC}"
if command_exists pg_isready; then
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PostgreSQL is running and accessible${NC}"
    else
        echo -e "${RED}PostgreSQL is not running or not accessible${NC}"
        echo -e "${YELLOW}To start PostgreSQL: brew services start postgresql${NC}"
        echo -e "${YELLOW}Or install PostgreSQL: brew install postgresql pgvector${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠ PostgreSQL tools not found - RSS clustering may not work${NC}"
    echo -e "${YELLOW}Install with: brew install postgresql pgvector${NC}"
fi

# Check if Redis Docker container is running
if ! docker ps --format "table {{.Names}}" | grep -q "^redis$"; then
    echo -e "${YELLOW}Starting Redis Docker container...${NC}"
    if command_exists docker; then
        # Try to start existing container first
        if docker ps -a --format "table {{.Names}}" | grep -q "^redis$"; then
            docker start redis
        else
            # Create new Redis container
            docker run -d --name redis -p 6379:6379 redis:alpine
        fi
        
        # Wait for Redis to be ready
        echo -e "${BLUE}Waiting for Redis to be ready...${NC}"
        for i in {1..10}; do
            if docker exec redis redis-cli ping > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
    else
        echo -e "${RED}Docker not found. Please install Docker and start it manually.${NC}"
        echo "  Or run: docker run -d --name redis -p 6379:6379 redis:alpine"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Redis Docker container is running${NC}"
fi

# Check if ports are available
if port_in_use 3000; then
    echo -e "${RED}Port 3000 is already in use. Please stop the process using it.${NC}"
    exit 1
fi

if port_in_use 8000; then
    echo -e "${RED}Port 8000 is already in use. Please stop the process using it.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"

# Create log directory
mkdir -p logs

# Start API server in background
echo -e "${BLUE}Starting FastAPI server...${NC}"
cd apps/api
echo -e "${YELLOW}Installing API dependencies with uv...${NC}"
uv sync --quiet

# Start API server and redirect output to log file
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../../logs/api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✓ API server started (PID: $API_PID)${NC}"

# Go back to root and start worker
cd ../..
echo -e "${BLUE}Starting worker agent...${NC}"
cd workers/agent
echo -e "${YELLOW}Installing worker dependencies with uv...${NC}"
uv sync --quiet

# Start Redis worker and redirect output to log file
uv run python worker.py > ../../logs/redis-worker.log 2>&1 &
REDIS_WORKER_PID=$!
echo -e "${GREEN}✓ Redis worker started (PID: $REDIS_WORKER_PID)${NC}"

# Start Celery worker and redirect output to log file  
uv run celery -A agent.celery_app worker --loglevel=info > ../../logs/celery-worker.log 2>&1 &
CELERY_WORKER_PID=$!
echo -e "${GREEN}✓ Celery worker started (PID: $CELERY_WORKER_PID)${NC}"

# Start Celery Beat scheduler for RSS polling and redirect output to log file
uv run celery -A agent.celery_app beat --loglevel=info > ../../logs/celery-beat.log 2>&1 &
CELERY_BEAT_PID=$!
echo -e "${GREEN}✓ Celery Beat scheduler started (PID: $CELERY_BEAT_PID)${NC}"

# Go back to root and start web app
cd ../..
echo -e "${BLUE}Starting Next.js web app...${NC}"
cd apps/web

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing web app dependencies...${NC}"
    npm install
fi

# Start web app and redirect output to log file
npm run dev > ../../logs/web.log 2>&1 &
WEB_PID=$!
echo -e "${GREEN}✓ Web app started (PID: $WEB_PID)${NC}"

cd ../..

# Save PIDs for cleanup script
echo "$API_PID" > .api.pid
echo "$REDIS_WORKER_PID" > .redis-worker.pid
echo "$CELERY_WORKER_PID" > .celery-worker.pid
echo "$CELERY_BEAT_PID" > .celery-beat.pid
echo "$WEB_PID" > .web.pid

# Wait for services to start
echo -e "${BLUE}Waiting for services to start...${NC}"
sleep 5

echo -e "${GREEN}🎉 YourCast is running!${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  • Web app: ${GREEN}http://localhost:3000${NC}"
echo -e "  • API server: ${GREEN}http://localhost:8000${NC}"
echo -e "  • API docs: ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  • API: ${YELLOW}tail -f logs/api.log${NC}"
echo -e "  • Redis Worker: ${YELLOW}tail -f logs/redis-worker.log${NC}"
echo -e "  • Celery Worker: ${YELLOW}tail -f logs/celery-worker.log${NC}"
echo -e "  • Celery Beat (RSS): ${YELLOW}tail -f logs/celery-beat.log${NC}"
echo -e "  • Web: ${YELLOW}tail -f logs/web.log${NC}"
echo ""
echo -e "${BLUE}To stop all services:${NC} ${YELLOW}./stop.sh${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop monitoring (services will continue running)${NC}"

# Monitor services
trap 'echo -e "\n${YELLOW}Services are still running in background. Use ./stop.sh to stop them.${NC}"; exit 0' INT

while true; do
    sleep 1
done
