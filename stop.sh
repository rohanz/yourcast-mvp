#!/bin/bash

# YourCast Development Stop Script
echo "🛑 Stopping YourCast development environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to kill process by PID if it exists
kill_process() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}Stopping $service_name (PID: $pid)...${NC}"
            kill "$pid"
            
            # Wait a bit and force kill if necessary
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${RED}Force killing $service_name...${NC}"
                kill -9 "$pid"
            fi
        else
            echo -e "${BLUE}$service_name was not running${NC}"
        fi
        rm -f "$pid_file"
    else
        echo -e "${BLUE}No PID file found for $service_name${NC}"
    fi
}

# Stop all services
kill_process ".api.pid" "API server"
kill_process ".redis-worker.pid" "Redis worker"
kill_process ".celery-worker.pid" "Celery worker"
kill_process ".celery-beat.pid" "Celery Beat scheduler"
kill_process ".web.pid" "Web app"

# Also try to kill any remaining processes on the ports
echo -e "${YELLOW}Checking for remaining processes on ports...${NC}"

# Kill any process on port 3000 (Next.js)
if lsof -i :3000 >/dev/null 2>&1; then
    echo -e "${YELLOW}Killing process on port 3000...${NC}"
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
fi

# Kill any process on port 8000 (FastAPI)
if lsof -i :8000 >/dev/null 2>&1; then
    echo -e "${YELLOW}Killing process on port 8000...${NC}"
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
fi

# Kill any remaining Python processes that might be workers
pkill -f "worker.py" 2>/dev/null || true
pkill -f "celery.*agent.celery_app" 2>/dev/null || true
pkill -f "uvicorn app.main" 2>/dev/null || true

# Clean up log files if they exist
if [ -d "logs" ]; then
    echo -e "${BLUE}Cleaning up log files...${NC}"
    rm -f logs/*.log
fi

echo -e "${GREEN}✅ All YourCast services stopped${NC}"
