# YourCast Development Guide

## Quick Start

### Start Everything
```bash
./start.sh
```

This will:
- ✅ Check and start Redis Docker container if needed
- ✅ Start the FastAPI server (port 8000)
- ✅ Start the Redis worker (job queue processor)
- ✅ Start the Celery worker (task processor)
- ✅ Start the Next.js web app (port 3000)
- ✅ Create log files for debugging

### Stop Everything
```bash
./stop.sh
```

This will cleanly shut down all services and clean up log files.

## Manual Commands (if needed)

### Start Individual Services

**API Server:**
```bash
cd apps/api
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Worker Agent:**
```bash
cd workers/agent
uv run python worker.py
# Or Celery worker:
uv run celery -A agent.celery_app worker --loglevel=info
```

**Web App:**
```bash
cd apps/web
npm run dev
```

**Redis (Docker):**
```bash
docker run -d --name redis -p 6379:6379 redis:alpine
# Or if container exists:
docker start redis
```

## Service URLs

- **Web App:** http://localhost:3000
- **API Server:** http://localhost:8000  
- **API Documentation:** http://localhost:8000/docs

## Debugging

### View Logs
```bash
# API logs
tail -f logs/api.log

# Redis worker logs  
tail -f logs/redis-worker.log

# Celery worker logs
tail -f logs/celery-worker.log

# Web app logs
tail -f logs/web.log
```

### Check Service Status
```bash
# Check what's running on ports
lsof -i :3000  # Web app
lsof -i :8000  # API server

# Check Redis (Docker)
docker exec redis redis-cli ping
```

## Prerequisites

- **Node.js** (for Next.js web app)
- **Python 3.8+** (for API server and worker)
- **uv** (Python package manager)
- **Docker** (for Redis container)
- **Redis Docker image** (for job queue and SSE state)

## Troubleshooting

### Port Already in Use
If you get a port conflict, use the stop script first:
```bash
./stop.sh
./start.sh
```

### Redis Docker Container Not Running
```bash
# Start existing container
docker start redis

# Or create new container
docker run -d --name redis -p 6379:6379 redis:alpine

# Check if it's running
docker exec redis redis-cli ping
```

### Dependencies Issues
The start script will automatically install dependencies with uv, but if you have issues:

```bash
# API dependencies
cd apps/api
uv sync

# Worker dependencies
cd workers/agent
uv sync

# Web dependencies
cd apps/web
npm install

# Install uv if not available
curl -LsSf https://astral.sh/uv/install.sh | sh
```
