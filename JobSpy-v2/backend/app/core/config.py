from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://user:password@localhost/jobspy"
    redis_url: str = "redis://localhost:6379"
    
    # AI Services
    openai_api_key: Optional[str] = None
    google_vision_api_key: Optional[str] = None
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Settings
    max_requests_per_minute: int = 100
    max_ai_requests_per_day: int = 1000
    
    class Config:
        env_file = ".env"

settings = Settings()