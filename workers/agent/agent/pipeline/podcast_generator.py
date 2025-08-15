import logging
import uuid
from typing import List, Dict, Any
from agent.services.smart_article_service import SmartArticleService
from agent.services.llm_service import LLMService
from agent.services.tts_service import TTSService
from agent.services.transcript_service import TranscriptService
from agent.services.storage_service import StorageService
from agent.services.episode_service import EpisodeService

logger = logging.getLogger(__name__)

class PodcastGenerator:
    def __init__(self, episode_service: EpisodeService):
        self.episode_service = episode_service
        self.smart_article_service = SmartArticleService()
        self.llm_service = LLMService()
        self.tts_service = TTSService()
        self.transcript_service = TranscriptService()
        self.storage_service = StorageService()
    
    def generate_episode(self, episode_id: str, subcategories: List[str], duration_minutes: int):
        """Execute the full podcast generation pipeline"""
        try:
            # Stage 1: Discover articles
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="discovering_articles", progress=10
            )
            # Use smart article service to get articles from our clustered database
            # Get articles filtered purely by the user's selected subcategories
            articles = self.smart_article_service.get_articles_by_subcategories(
                selected_subcategories=subcategories,
                total_articles=8,  # More articles for better content variety
                min_importance_score=4  # Minimum quality threshold
            )
            logger.info(f"Found {len(articles)} articles for episode {episode_id}")
            
            # Stage 2: Convert articles to sources format expected by LLM service
            self.episode_service.set_episode_status(
                episode_id, "processing", stage="extracting_content", progress=20
            )
            sources = self._convert_articles_to_sources(articles)
            article_to_source_map = self.episode_service.store_sources(episode_id, sources)
            
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
            title = self.llm_service.generate_title(subcategories, script)
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
            self.episode_service.store_episode_segments(episode_id, transcript_data, article_to_source_map)
            
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
    
    def _convert_articles_to_sources(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert smart article service format to sources format expected by LLM service"""
        sources = []
        
        for article in articles:
            # Create source in the format expected by LLM service
            source = {
                "id": article.get("article_id", str(uuid.uuid4())),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "published_date": article.get("publication_timestamp", ""),
                "excerpt": article.get("summary", "")[:200] + "..." if len(article.get("summary", "")) > 200 else article.get("summary", ""),
                "full_text": article.get("summary", ""),  # Use summary as full text for now
                "source_name": article.get("source_name", "Unknown"),
                "summary": article.get("summary", ""),
                # Additional metadata from our smart system
                "category": article.get("category", ""),
                "subcategory": article.get("subcategory", ""),
                "importance_score": article.get("importance_score", 5),
                "story_title": article.get("story_title", ""),
                "cluster_id": article.get("cluster_id", ""),
                "tags": article.get("tags", [])
            }
            sources.append(source)
            
        logger.info(f"Converted {len(sources)} articles to sources format")
        return sources
