import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Use absolute path for database to avoid working directory issues
    # Go up from app/config.py -> app/ -> api/ -> apps/ -> project root -> shared/
    _config_dir = os.path.dirname(os.path.abspath(__file__))
    _app_dir = os.path.dirname(_config_dir)
    _api_dir = os.path.dirname(_app_dir)
    _apps_dir = os.path.dirname(_api_dir)
    _project_root = os.path.dirname(_apps_dir)
    _db_path = os.path.join(_project_root, "shared", "yourcast.db")
    database_url: str = os.getenv("DATABASE_URL", f"sqlite:///{_db_path}")
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    google_tts_api_key: str = os.getenv("GOOGLE_TTS_API_KEY", "")
    
    # Local storage directory for files - use shared directory
    storage_dir: str = os.getenv("STORAGE_DIR", "../../shared/storage")
    
    class Config:
        env_file = ".env"

settings = Settings()