import logging
import json
import os
import shutil
from typing import List, Dict, Any
from agent.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.storage_dir = settings.storage_dir
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "transcripts"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "vtt"), exist_ok=True)
    
    def upload_audio(self, episode_id: str, audio_path: str) -> str:
        """Copy audio file to local storage"""
        try:
            # Create episode directory
            episode_dir = os.path.join(self.storage_dir, "audio")
            os.makedirs(episode_dir, exist_ok=True)
            
            # Copy file to storage
            storage_path = os.path.join(episode_dir, f"{episode_id}.mp3")
            shutil.copy2(audio_path, storage_path)
            
            # Clean up temporary file
            os.remove(audio_path)
            
            # Return absolute URL for serving
            absolute_url = f"http://localhost:8000/storage/audio/{episode_id}.mp3"
            
            logger.info(f"Stored audio for episode {episode_id} at {storage_path}")
            return absolute_url
            
        except Exception as e:
            logger.error(f"Failed to store audio for episode {episode_id}: {str(e)}")
            raise
    
    def upload_transcript(self, episode_id: str, transcript_data: List[Dict[str, Any]]) -> str:
        """Save transcript JSON to local storage"""
        try:
            # Create episode directory
            episode_dir = os.path.join(self.storage_dir, "transcripts")
            os.makedirs(episode_dir, exist_ok=True)
            
            # Save transcript
            storage_path = os.path.join(episode_dir, f"{episode_id}.json")
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            # Return absolute URL for serving
            absolute_url = f"http://localhost:8000/storage/transcripts/{episode_id}.json"
            
            logger.info(f"Stored transcript for episode {episode_id} at {storage_path}")
            return absolute_url
            
        except Exception as e:
            logger.error(f"Failed to store transcript for episode {episode_id}: {str(e)}")
            raise
    
    def upload_vtt(self, episode_id: str, vtt_content: str) -> str:
        """Save WebVTT file to local storage"""
        try:
            # Create episode directory
            episode_dir = os.path.join(self.storage_dir, "vtt")
            os.makedirs(episode_dir, exist_ok=True)
            
            # Save VTT file
            storage_path = os.path.join(episode_dir, f"{episode_id}.vtt")
            with open(storage_path, 'w', encoding='utf-8') as f:
                f.write(vtt_content)
            
            # Return absolute URL for serving
            absolute_url = f"http://localhost:8000/storage/vtt/{episode_id}.vtt"
            
            logger.info(f"Stored VTT for episode {episode_id} at {storage_path}")
            return absolute_url
            
        except Exception as e:
            logger.error(f"Failed to store VTT for episode {episode_id}: {str(e)}")
            raise