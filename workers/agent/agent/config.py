import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Database configuration - PostgreSQL with pgvector for RSS clustering
    # Use absolute path for database to avoid working directory issues
    # Go up from agent/config.py -> agent/ -> workers/ -> project root -> shared/
    _config_dir = os.path.dirname(os.path.abspath(__file__))
    _agent_dir = os.path.dirname(_config_dir)
    _workers_dir = os.path.dirname(_agent_dir)
    _project_root = os.path.dirname(_workers_dir)
    _db_path = os.path.join(_project_root, "shared", "yourcast.db")
    
    # Default to PostgreSQL for RSS clustering, fallback to SQLite
    database_url = os.getenv("DATABASE_URL", "postgresql://yourcast_user:yourcast_password@localhost:5432/yourcast_db")
    
    # Google Cloud AI Configuration
    google_cloud_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    google_cloud_location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    
    # API Keys
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    news_api_key = os.getenv("NEWS_API_KEY", "")  # Optional - RSS feeds are primary
    google_tts_api_key = os.getenv("GOOGLE_TTS_API_KEY", "")
    
    # Local storage directory for files - use shared directory
    storage_dir = os.getenv("STORAGE_DIR", "../../shared/storage")
    
    # RSS feeds for fallback - now using categorized feeds
    # Import here to avoid circular import
    @property
    def rss_feeds(self):
        from agent.rss_config import get_all_feeds
        return get_all_feeds()

settings = Settings()