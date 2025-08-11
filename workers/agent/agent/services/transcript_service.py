import logging
import tempfile
import os
from typing import List, Dict, Any
from agent.services.llm_service import PodcastScript

logger = logging.getLogger(__name__)

class TranscriptService:
    def __init__(self):
        pass
    
    def generate_forced_alignment(self, audio_path: str, script: PodcastScript) -> List[Dict[str, Any]]:
        """Generate timestamps using estimated timing (simplified for MVP)"""
        # For MVP, we'll use estimated timing instead of Whisper
        return self._create_fallback_segments(script)
    
    def _group_into_sentences(self, word_entries: List[Dict]) -> List[Dict[str, Any]]:
        """Group word-level timestamps into sentence-level segments"""
        if not word_entries:
            return []
        
        segments = []
        current_segment = {
            "start": word_entries[0]["start"],
            "text": "",
            "words": []
        }
        
        for word_entry in word_entries:
            current_segment["words"].append(word_entry)
            current_segment["text"] += word_entry["text"]
            
            # End segment on sentence boundaries or after ~15 words
            if (word_entry["text"].endswith(('.', '!', '?')) or 
                len(current_segment["words"]) >= 15):
                
                current_segment["end"] = word_entry["end"]
                segments.append(current_segment)
                
                # Start new segment
                if word_entry != word_entries[-1]:  # Not the last word
                    current_segment = {
                        "start": word_entry["end"],
                        "text": "",
                        "words": []
                    }
        
        # Handle any remaining words
        if current_segment["words"]:
            current_segment["end"] = current_segment["words"][-1]["end"]
            segments.append(current_segment)
        
        return segments
    
    def _add_source_attribution(self, segments: List[Dict], script: PodcastScript) -> List[Dict[str, Any]]:
        """Add source IDs to segments based on script paragraphs"""
        attributed_segments = []
        script_text = " ".join([p["text"] for p in script.paragraphs])
        
        for i, segment in enumerate(segments):
            # Try to match segment text to script paragraphs
            source_ids = []
            segment_text = segment["text"].strip()
            
            for paragraph in script.paragraphs:
                # Simple text matching - could be improved
                if any(word in paragraph["text"].lower() for word in segment_text.lower().split()[:3]):
                    source_ids.extend(paragraph["source_ids"])
            
            attributed_segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment_text,
                "source_ids": list(set(source_ids))  # Remove duplicates
            })
        
        return attributed_segments
    
    def _create_fallback_segments(self, script: PodcastScript) -> List[Dict[str, Any]]:
        """Create segments with estimated timing as fallback"""
        segments = []
        current_time = 0.0
        words_per_second = 2.67  # 160 WPM / 60 seconds
        
        for paragraph in script.paragraphs:
            word_count = len(paragraph["text"].split())
            duration = word_count / words_per_second
            
            segments.append({
                "start": current_time,
                "end": current_time + duration,
                "text": paragraph["text"],
                "source_ids": paragraph["source_ids"]
            })
            
            current_time += duration + 0.5  # Add small pause
        
        logger.warning("Using fallback timing estimation")
        return segments
    
    def generate_webvtt(self, transcript_data: List[Dict[str, Any]]) -> str:
        """Generate WebVTT file content for chapters"""
        vtt_content = "WEBVTT\n\n"
        
        for i, segment in enumerate(transcript_data):
            start_time = self._format_webvtt_time(segment["start"])
            end_time = self._format_webvtt_time(segment["end"])
            
            # Create chapter markers for longer segments
            if segment["end"] - segment["start"] > 10:  # 10+ second segments
                vtt_content += f"{start_time} --> {end_time}\n"
                vtt_content += f"{segment['text'][:50]}...\n\n"
        
        return vtt_content
    
    def _format_webvtt_time(self, seconds: float) -> str:
        """Format seconds as WebVTT timestamp"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"