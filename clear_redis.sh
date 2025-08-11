#!/bin/bash

echo "Clearing Redis queues..."
docker exec redis redis-cli flushall

echo "Redis cleared successfully!"
echo ""
echo "You can now start fresh with:"
echo "1. Run Celery worker: cd workers/agent && uv run celery -A agent.celery_app worker --loglevel=info"
echo "2. Run API server: cd apps/api && uv run fastapi dev main.py --host 0.0.0.0 --port 8000"
echo "3. Run frontend: cd apps/web && npm run dev"
