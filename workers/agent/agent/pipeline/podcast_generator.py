import logging
import uuid
from typing import List, Dict, Any
from agent.services.news_service import NewsService
from agent.services.llm_service import LLMService
from agent.services.tts_service import TTSService
from agent.services.transcript_service import TranscriptService
from agent.services.storage_service import StorageService
from agent.services.episode_service import EpisodeService

logger = logging.getLogger(__name__)

class PodcastGenerator:
    def __init__(self, episode_service: EpisodeService):
        self.episode_service = episode_service
        self.news_service = NewsService()
        self.llm_service = LLMService()
        self.tts_service = TTSService()
        self.transcript_service = TranscriptService()
        self.storage_service = StorageService()
    
    def generate_episode(self, episode_id: str, topics: List[str], duration_minutes: int):
        """Execute the full podcast generation pipeline"""
        try:
            # Stage 1: Discover articles
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="discovering_articles", progress=10
            )
            articles = self.news_service.discover_articles(topics, limit=5)
            logger.info(f"Found {len(articles)} articles for episode {episode_id}")
            
            # Stage 2: Extract and store article content
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="extracting_content", progress=20
            )
            sources = self.news_service.extract_article_content(articles)
            self.episode_service.store_sources(episode_id, sources)
            
            # Stage 3: Generate script
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="generating_script", progress=40
            )
            script = self.llm_service.generate_podcast_script(sources, duration_minutes)
            
            # Stage 4: Convert to audio
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="generating_audio", progress=60
            )
            audio_chunks = self.tts_service.generate_audio_chunks(script.paragraphs)
            combined_audio_path = self.tts_service.combine_audio_chunks(audio_chunks)
            
            # Stage 5: Generate timestamps and WebVTT
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="generating_timestamps", progress=80
            )
            transcript_data = self.transcript_service.generate_forced_alignment(
                combined_audio_path, script
            )
            vtt_content = self.transcript_service.generate_webvtt(transcript_data)
            
            # Stage 6: Upload files
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="uploading_files", progress=90
            )
            audio_url = self.storage_service.upload_audio(episode_id, combined_audio_path)
            transcript_url = self.storage_service.upload_transcript(episode_id, transcript_data)
            vtt_url = self.storage_service.upload_vtt(episode_id, vtt_content)
            
            # Stage 7: Update episode with final data
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="finalizing", progress=95
            )
            
            # Generate title and description from script
            title = self.llm_service.generate_title(topics, script)
            description = self.llm_service.generate_description(sources, script)
            
            # Update episode in database
            self.episode_service.update_episode(
                episode_id=episode_id,
                title=title,
                description=description,
                duration_seconds=int(transcript_data[-1]["end"]),
                audio_url=audio_url,
                transcript_url=transcript_url,
                vtt_url=vtt_url,
                status="completed"
            )
            
            # Store episode segments for chapter navigation
            self.episode_service.store_episode_segments(episode_id, transcript_data)
            
            # Final status update
            self.episode_service.set_episode_status(
                episode_id, "completed", stage="completed", progress=100
            )
            
            logger.info(f"Successfully generated podcast episode {episode_id}")
            
        except Exception as e:
            logger.error(f"Pipeline failed for episode {episode_id}: {str(e)}")
            self.episode_service.set_episode_status(
                episode_id, "failed", error=str(e)
            )
            raise