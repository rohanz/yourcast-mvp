import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models import Episode, EpisodeSegment, Source
from app.schemas import (
    CreateEpisodeRequest,
    CreateEpisodeResponse,
    EpisodeSchema,
    EpisodeSegmentSchema,
    SourceSchema,
    EpisodeStatusEvent,
)
from app.services.episode_service import EpisodeService
import json
import asyncio

router = APIRouter()

@router.post("", response_model=CreateEpisodeResponse)
def create_episode(
    request: CreateEpisodeRequest,
    db: Session = Depends(get_db)
):
    # Create episode record
    episode_id = str(uuid.uuid4())
    episode = Episode(
        id=episode_id,
        title="Generating...",
        description="Your micro-podcast is being generated",
        topics=request.topics,
        status="pending"
    )
    
    db.add(episode)
    db.commit()
    
    # Queue episode generation job
    episode_service = EpisodeService()
    episode_service.queue_episode_generation(episode_id, request.topics, request.duration_minutes)
    
    return CreateEpisodeResponse(episode_id=episode_id, status="pending")

@router.get("/{episode_id}", response_model=EpisodeSchema)
def get_episode(episode_id: str, db: Session = Depends(get_db)):
    # Force fresh query by expiring the session
    db.expire_all()
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    
    # Check Redis for updated status or populate missing URLs for completed episodes
    if episode.status == "pending":
        episode_service = EpisodeService()
        status_event = episode_service.get_episode_status_event(episode_id)
        if status_event and status_event.status in ["completed", "failed"]:
            # Update database with latest status from Redis
            episode.status = status_event.status
            if status_event.status == "completed":
                # Update other fields if available
                episode.title = "Generated Podcast"  # Could be improved
                episode.description = "Your micro-podcast has been generated"
                # Set file URLs pointing to Python API server
                episode.audio_url = f"http://localhost:8000/storage/audio/{episode_id}.mp3"
                episode.transcript_url = f"http://localhost:8000/storage/transcripts/{episode_id}.json"
                episode.vtt_url = f"http://localhost:8000/storage/vtt/{episode_id}.vtt"
                episode.duration_seconds = 120  # Placeholder - could be improved
            db.commit()
    elif episode.status == "completed" and not episode.audio_url:
        # Fix completed episodes that are missing file URLs
        episode.audio_url = f"http://localhost:8000/storage/audio/{episode_id}.mp3"
        episode.transcript_url = f"http://localhost:8000/storage/transcripts/{episode_id}.json"
        episode.vtt_url = f"http://localhost:8000/storage/vtt/{episode_id}.vtt"
        if episode.duration_seconds == 0:
            episode.duration_seconds = 120  # Placeholder - could be improved
        db.commit()
    
    return EpisodeSchema.from_orm(episode)

@router.get("/{episode_id}/segments", response_model=List[EpisodeSegmentSchema])
def get_episode_segments(episode_id: str, db: Session = Depends(get_db)):
    segments = (
        db.query(EpisodeSegment)
        .filter(EpisodeSegment.episode_id == episode_id)
        .order_by(EpisodeSegment.order_index)
        .all()
    )
    
    return [EpisodeSegmentSchema.from_orm(segment) for segment in segments]

@router.get("/{episode_id}/sources", response_model=List[SourceSchema])
def get_episode_sources(episode_id: str, db: Session = Depends(get_db)):
    sources = db.query(Source).filter(Source.episode_id == episode_id).all()
    return [SourceSchema.from_orm(source) for source in sources]

@router.get("/{episode_id}/events")
async def get_episode_events(episode_id: str):
    """Server-Sent Events endpoint for episode status updates"""
    
    async def event_generator():
        episode_service = EpisodeService()
        
        while True:
            try:
                # Check episode status
                event = episode_service.get_episode_status_event(episode_id)
                
                if event:
                    yield f"data: {json.dumps(event.dict())}\n\n"
                    
                    # Stop streaming if episode is completed or failed
                    if event.status in ["completed", "failed"]:
                        break
                        
                await asyncio.sleep(2)  # Poll every 2 seconds
                
            except Exception as e:
                error_event = EpisodeStatusEvent(
                    episode_id=episode_id,
                    status="error",
                    error=str(e)
                )
                yield f"data: {json.dumps(error_event.dict())}\n\n"
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )