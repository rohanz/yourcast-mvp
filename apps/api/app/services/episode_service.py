import redis
from typing import List, Optional
from app.config import settings
from app.schemas import EpisodeStatusEvent
import json

class EpisodeService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
    
    def queue_episode_generation(self, episode_id: str, topics: List[str], duration_minutes: int):
        """Queue episode generation job"""
        job_data = {
            "episode_id": episode_id,
            "topics": topics,
            "duration_minutes": duration_minutes
        }
        
        # Add to Redis queue (will be consumed by worker)
        self.redis_client.lpush("episode_queue", json.dumps(job_data))
        
        # Set initial status
        self.set_episode_status(episode_id, "processing", stage="queued")
    
    def set_episode_status(self, episode_id: str, status: str, stage: Optional[str] = None, progress: Optional[int] = None, error: Optional[str] = None):
        """Update episode status in Redis"""
        status_data = {
            "episode_id": episode_id,
            "status": status,
            "stage": stage,
            "progress": progress,
            "error": error
        }
        
        key = f"episode_status:{episode_id}"
        self.redis_client.setex(key, 3600, json.dumps(status_data))  # Expire in 1 hour
    
    def get_episode_status_event(self, episode_id: str) -> Optional[EpisodeStatusEvent]:
        """Get current episode status"""
        key = f"episode_status:{episode_id}"
        status_data = self.redis_client.get(key)
        
        if status_data:
            data = json.loads(status_data)
            return EpisodeStatusEvent(**data)
        
        return None