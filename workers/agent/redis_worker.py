#!/usr/bin/env python3
"""
Redis Queue Worker - Processes jobs from Redis queue and forwards to Celery
"""

import logging
import json
import redis
import time
from agent.config import settings
from agent.celery_app import app

logger = logging.getLogger(__name__)

def start_worker():
    """Simple Redis queue worker for development"""
    
    redis_client = redis.from_url(settings.redis_url)
    logger.info("Starting Redis queue worker...")
    
    while True:
        try:
            # Block until job available
            job_data = redis_client.brpop("episode_queue", timeout=5)
            
            if job_data:
                _, job_json = job_data
                job = json.loads(job_json)
                
                episode_id = job["episode_id"]
                # Handle both old (topics) and new (subcategories) format
                subcategories = job.get("subcategories") or job.get("topics", [])
                duration_minutes = job["duration_minutes"]
                
                logger.info(f"Processing job for episode {episode_id}")
                # Call task by name to ensure correct registration
                app.send_task('agent.tasks.generate_podcast', args=[episode_id, subcategories, duration_minutes])
                
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    start_worker()
