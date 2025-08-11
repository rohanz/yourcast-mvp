import logging
import json
from typing import List
from celery import current_task
from agent.celery_app import app
from agent.pipeline.podcast_generator import PodcastGenerator
from agent.services.episode_service import EpisodeService

logger = logging.getLogger(__name__)

@app.task(bind=True)
def generate_podcast(self, episode_id: str, topics: List[str], duration_minutes: int):
    """Generate podcast episode task"""
    try:
        logger.info(f"Starting podcast generation for episode {episode_id}")
        
        episode_service = EpisodeService()
        generator = PodcastGenerator(episode_service)
        
        # Update status to processing
        episode_service.set_episode_status(
            episode_id, "processing", stage="started", progress=0
        )
        
        # Execute pipeline
        generator.generate_episode(episode_id, topics, duration_minutes)
        
        logger.info(f"Completed podcast generation for episode {episode_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate podcast for episode {episode_id}: {str(e)}")
        episode_service = EpisodeService()
        episode_service.set_episode_status(
            episode_id, "failed", error=str(e)
        )
        raise

# Simple Redis-based worker that processes jobs directly
def start_worker():
    """Simple Redis queue worker for development"""
    import redis
    import time
    from agent.config import settings
    
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
                topics = job["topics"]
                duration_minutes = job["duration_minutes"]
                
                logger.info(f"Processing job for episode {episode_id}")
                generate_podcast.delay(episode_id, topics, duration_minutes)
                
        except Exception as e:
            logger.error(f"Worker error: {str(e)}")
            time.sleep(5)

if __name__ == "__main__":
    start_worker()