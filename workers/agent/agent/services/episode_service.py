import logging
import uuid
import json
import redis
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from agent.config import settings

logger = logging.getLogger(__name__)

# Define database models to match API exactly
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)  # Optional for MVP
    title = Column(String, nullable=False)
    description = Column(Text)
    duration_seconds = Column(Integer, default=0)
    topics = Column(JSON, nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    audio_url = Column(String)
    transcript_url = Column(String)
    vtt_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EpisodeSegment(Base):
    __tablename__ = "episode_segments"
    
    id = Column(String, primary_key=True)
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=False)
    start_time = Column(Integer, nullable=False)
    end_time = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    source_id = Column(String, ForeignKey("sources.id"), nullable=True)
    order_index = Column(Integer, nullable=False)

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True)
    episode_id = Column(String, ForeignKey("episodes.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, nullable=False)
    published_date = Column(DateTime)
    excerpt = Column(Text)
    summary = Column(Text)

logger.info("Using standalone database models for worker")

class EpisodeService:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url)
        
        # Database setup
        logger.info(f"Worker using database: {settings.database_url}")
        self.engine = create_engine(settings.database_url)
        Base.metadata.create_all(self.engine, checkfirst=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal
    
    def set_episode_status(self, episode_id: str, status: str, stage: Optional[str] = None, 
                          progress: Optional[int] = None, error: Optional[str] = None):
        """Update episode status in Redis"""
        status_data = {
            "episode_id": episode_id,
            "status": status,
            "stage": stage,
            "progress": progress,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        key = f"episode_status:{episode_id}"
        self.redis_client.setex(key, 3600, json.dumps(status_data))  # Expire in 1 hour
        logger.info(f"Episode {episode_id} status: {status} - {stage}")
    
    def store_sources(self, episode_id: str, sources_data: List[Dict[str, Any]]):
        """Store article sources in database"""
        db = self.db_session()
        try:
            for source_data in sources_data:
                source = Source(
                    id=source_data["id"],
                    episode_id=episode_id,
                    title=source_data["title"],
                    url=source_data["url"],
                    published_date=datetime.fromisoformat(source_data["published_date"].replace('Z', '+00:00')) if source_data["published_date"] else None,
                    excerpt=source_data["excerpt"],
                    summary=source_data.get("summary", "")
                )
                db.add(source)
            
            db.commit()
            logger.info(f"Stored {len(sources_data)} sources for episode {episode_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store sources: {str(e)}")
            raise
        finally:
            db.close()
    
    def update_episode(self, episode_id: str, **updates):
        """Update episode record in database"""
        db = self.db_session()
        try:
            episode = db.query(Episode).filter(Episode.id == episode_id).first()
            if not episode:
                logger.error(f"Episode {episode_id} not found in database. Available episodes: {[ep.id for ep in db.query(Episode).all()]}")
                # Try to create a basic episode record if it doesn't exist
                episode = Episode(
                    id=episode_id,
                    title="Generated Podcast",
                    description="Podcast generated by worker",
                    topics=[],
                    status="processing"
                )
                db.add(episode)
                db.flush()  # Make sure the episode is available for updates
            
            for key, value in updates.items():
                if hasattr(episode, key):
                    setattr(episode, key, value)
            
            db.commit()
            logger.info(f"Updated episode {episode_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update episode: {str(e)}")
            raise
        finally:
            db.close()
    
    def store_episode_segments(self, episode_id: str, transcript_data: List[Dict[str, Any]]):
        """Store episode segments for chapter navigation"""
        db = self.db_session()
        try:
            # Clear existing segments
            db.query(EpisodeSegment).filter(EpisodeSegment.episode_id == episode_id).delete()
            
            for i, segment_data in enumerate(transcript_data):
                # Only create segments for longer sections (for chapter navigation)
                if segment_data["end"] - segment_data["start"] > 10:  # 10+ seconds
                    segment = EpisodeSegment(
                        id=str(uuid.uuid4()),
                        episode_id=episode_id,
                        start_time=int(segment_data["start"]),
                        end_time=int(segment_data["end"]),
                        text=segment_data["text"][:500],  # Truncate for storage
                        source_id=segment_data["source_ids"][0] if segment_data["source_ids"] else None,
                        order_index=i
                    )
                    db.add(segment)
            
            db.commit()
            logger.info(f"Stored episode segments for {episode_id}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to store segments: {str(e)}")
            raise
        finally:
            db.close()