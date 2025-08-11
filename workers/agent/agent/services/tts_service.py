import logging
import tempfile
import os
import requests
from typing import List, Dict, Any
from pydub import AudioSegment
from agent.config import settings

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self):
        self.api_key = settings.google_tts_api_key
        if not self.api_key:
            raise ValueError("Google TTS API key is required")
    
    def generate_audio_chunks(self, paragraphs: List[Dict[str, Any]]) -> List[str]:
        """Convert script paragraphs to audio chunks"""
        audio_files = []
        
        for i, paragraph in enumerate(paragraphs):
            try:
                audio_path = self._text_to_speech(paragraph["text"], f"chunk_{i}")
                audio_files.append(audio_path)
                logger.info(f"Generated audio for paragraph {i+1}/{len(paragraphs)}")
            except Exception as e:
                logger.error(f"Failed to generate audio for paragraph {i}: {str(e)}")
                # Create a short silence as fallback
                silence_path = self._create_silence(2.0, f"silence_{i}")
                audio_files.append(silence_path)
        
        return audio_files
    
    def _text_to_speech(self, text: str, filename: str) -> str:
        """Convert text to speech using Google Cloud TTS REST API"""
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        
        # Request payload
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": "en-US",
                "name": "en-US-Neural2-F",  # High quality neural voice (female)
                "ssmlGender": "FEMALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": 1.0,
                "pitch": 0.0
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Make API request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Get the audio content (base64 encoded)
        result = response.json()
        audio_content = result["audioContent"]
        
        # Decode base64 and save to file
        import base64
        audio_data = base64.b64decode(audio_content)
        
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{filename}.mp3")
        
        with open(audio_path, "wb") as f:
            f.write(audio_data)
        
        logger.debug(f"Audio saved to {audio_path}")
        return audio_path
    
    def _create_silence(self, duration_seconds: float, filename: str) -> str:
        """Create a silent audio segment"""
        silence = AudioSegment.silent(duration=int(duration_seconds * 1000))
        
        temp_dir = tempfile.gettempdir()
        audio_path = os.path.join(temp_dir, f"{filename}.mp3")
        
        silence.export(audio_path, format="mp3")
        return audio_path
    
    def combine_audio_chunks(self, audio_files: List[str]) -> str:
        """Combine audio chunks into a single file"""
        combined_audio = AudioSegment.empty()
        
        for audio_file in audio_files:
            try:
                segment = AudioSegment.from_mp3(audio_file)
                combined_audio += segment
                
                # Add small pause between segments
                pause = AudioSegment.silent(duration=500)  # 0.5 seconds
                combined_audio += pause
                
            except Exception as e:
                logger.warning(f"Failed to load audio file {audio_file}: {str(e)}")
                continue
        
        # Export combined audio
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "combined_podcast.mp3")
        
        combined_audio.export(output_path, format="mp3", bitrate="128k")
        
        # Clean up individual chunks
        for audio_file in audio_files:
            try:
                os.remove(audio_file)
            except:
                pass
        
        logger.info(f"Combined audio saved to {output_path}")
        return output_path