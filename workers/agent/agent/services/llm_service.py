import logging
import google.generativeai as genai
from typing import List, Dict, Any
from dataclasses import dataclass
from agent.config import settings

logger = logging.getLogger(__name__)

@dataclass
class PodcastScript:
    paragraphs: List[Dict[str, Any]]
    estimated_duration: int

class LLMService:
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_podcast_script(self, sources: List[Dict[str, Any]], duration_minutes: int) -> PodcastScript:
        """Generate a podcast script from news sources"""
        target_words = duration_minutes * 160  # 160 WPM target
        
        # First, summarize each article
        summaries = []
        for source in sources:
            try:
                summary = self._summarize_article(source["full_text"], source["title"])
                summaries.append({
                    "source_id": source["id"],
                    "title": source["title"],
                    "summary": summary,
                    "url": source["url"]
                })
            except Exception as e:
                logger.warning(f"Failed to summarize article {source['title']}: {str(e)}")
                continue
        
        # Generate the narrative script
        script_prompt = self._build_script_prompt(summaries, target_words, duration_minutes)
        
        try:
            response = self.model.generate_content(script_prompt)
            script_text = response.text
        except Exception as e:
            logger.error(f"Failed to generate script with Gemini: {str(e)}")
            raise
        
        # Parse the script into paragraphs with source citations
        paragraphs = self._parse_script_paragraphs(script_text, summaries)
        
        return PodcastScript(
            paragraphs=paragraphs,
            estimated_duration=duration_minutes * 60  # Convert to seconds
        )
    
    def _summarize_article(self, full_text: str, title: str) -> str:
        """Summarize a single article"""
        prompt = f"""
        Please provide a concise summary of this news article in 2-3 bullet points. Focus on the key facts and developments.
        
        Title: {title}
        
        Article:
        {full_text[:2000]}  # Truncate to fit context
        
        Summary (as bullet points):
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to summarize article with Gemini: {str(e)}")
            # Fallback summary
            return f"• {title}\n• Key developments in this story\n• Further details available"
    
    def _build_script_prompt(self, summaries: List[Dict], target_words: int, duration_minutes: int) -> str:
        """Build the prompt for script generation"""
        sources_text = "\n\n".join([
            f"Source {i+1} - {s['title']}:\n{s['summary']}\nURL: {s['url']}"
            for i, s in enumerate(summaries)
        ])
        
        return f"""
        Create a {duration_minutes}-minute podcast script from these news articles. The script should:
        
        1. Be approximately {target_words} words (targeting 160 words per minute)
        2. Flow as a single narrative voice (no intro/outro music needed)
        3. Include natural transitions between topics
        4. Cite sources naturally in the narrative (e.g., "According to Reuters..." or "As reported by BBC...")
        5. Be engaging and conversational while remaining informative
        6. Focus on the most important and interesting developments
        
        News Sources:
        {sources_text}
        
        Write the complete script in a natural, flowing narrative style. Format it as clear paragraphs that can be easily read aloud.
        """
    
    def _parse_script_paragraphs(self, script_text: str, summaries: List[Dict]) -> List[Dict[str, Any]]:
        """Parse script into paragraphs with source attribution"""
        paragraphs = []
        script_paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip()]
        
        for paragraph_text in script_paragraphs:
            # Try to identify which sources are referenced in this paragraph
            source_ids = []
            
            for summary in summaries:
                # Simple heuristic: if title keywords or source name mentioned
                title_words = summary["title"].lower().split()[:3]  # First 3 words of title
                
                if any(word in paragraph_text.lower() for word in title_words if len(word) > 3):
                    source_ids.append(summary["source_id"])
            
            paragraphs.append({
                "text": paragraph_text,
                "source_ids": source_ids
            })
        
        return paragraphs
    
    def generate_title(self, topics: List[str], script: PodcastScript) -> str:
        """Generate an engaging title for the episode"""
        topics_text = ", ".join(topics)
        script_preview = " ".join([p["text"] for p in script.paragraphs])[:500]
        
        prompt = f"""
        Generate a compelling podcast episode title based on these topics and script preview.
        
        Topics: {topics_text}
        
        Script preview: {script_preview}...
        
        The title should be:
        - Engaging and clickable
        - Under 60 characters
        - Reflective of the main stories covered
        - Professional but accessible
        
        Return just the title, no quotes or extra text.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip().strip('"')
        except Exception as e:
            logger.error(f"Failed to generate title with Gemini: {str(e)}")
            # Fallback title
            return f"News Update: {', '.join(topics)}"
    
    def generate_description(self, sources: List[Dict], script: PodcastScript) -> str:
        """Generate episode description"""
        source_titles = [s["title"] for s in sources[:3]]  # Top 3 sources
        
        return f"A 5-minute news update covering: {', '.join(source_titles)}. Generated from the latest articles and delivered in an easy-to-listen format."
    
    def generate_text(self, prompt: str) -> str:
        """Generate text response for clustering and categorization tasks"""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate text with Gemini: {str(e)}")
            raise
