import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Use absolute path for database to avoid working directory issues
    # Go up from agent/config.py -> agent/ -> workers/ -> project root -> shared/
    _config_dir = os.path.dirname(os.path.abspath(__file__))
    _agent_dir = os.path.dirname(_config_dir)
    _workers_dir = os.path.dirname(_agent_dir)
    _project_root = os.path.dirname(_workers_dir)
    _db_path = os.path.join(_project_root, "shared", "yourcast.db")
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")
    news_api_key = os.getenv("NEWS_API_KEY", "")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    google_tts_api_key = os.getenv("GOOGLE_TTS_API_KEY", "")
    
    # Optional: Google Cloud credentials path (fallback)
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # Local storage directory for files - use shared directory
    storage_dir = os.getenv("STORAGE_DIR", "../../shared/storage")
    
    # RSS feeds for fallback
    rss_feeds = [
        "http://feeds.bbci.co.uk/news/rss.xml",
        "https://feeds.reuters.com/reuters/topNews",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.npr.org/1001/rss.xml",
    ]

settings = Settings()