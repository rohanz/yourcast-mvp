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

# Check PostgreSQL
psql yourcast_db -c "SELECT COUNT(*) FROM articles;"
```

## RSS Discovery Testing

The system now features an advanced RSS discovery and clustering pipeline. Use these commands to test it:

### Basic RSS Discovery Test
```bash
cd workers/agent
# Run small discovery test (5 feeds, 3 articles each)
uv run test_small_discovery.py
```

### Debug Mode with LLM Response Logging
```bash
# Enable debug logging to see AI clustering decisions
uv run test_small_discovery_debug.py
```

### Manual RSS Testing
```bash
# Test specific RSS feeds
uv run test_manual_rss.py
```

### Clear Database
```bash
# Clear all articles and clusters (useful for testing)
uv run clear_database.py
```

### Database Inspection
```bash
# Connect to PostgreSQL database
psql yourcast_db

# View recent articles with clustering info
SELECT title, source_name, subcategory, tags, created_at 
FROM articles 
ORDER BY created_at DESC 
LIMIT 10;

# View story clusters
SELECT cluster_id, canonical_title, 
       (SELECT COUNT(*) FROM articles WHERE cluster_id = sc.cluster_id) as article_count
FROM story_clusters sc 
ORDER BY created_at DESC;
```

## Prerequisites

- **Node.js** (for Next.js web app)
- **Python 3.11+** (for API server and worker)
- **PostgreSQL 14+** with **pgvector extension** (for RSS clustering)
- **uv** (Python package manager)
- **Docker** (for Redis container)
- **Redis Docker image** (for job queue and SSE state)
- **Google Cloud service account** (for AI services)

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

### PostgreSQL Not Running
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL service
brew services start postgresql

# Stop PostgreSQL service (if needed)
brew services stop postgresql

# Test connection
psql yourcast_db -c "SELECT COUNT(*) FROM articles;"
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
