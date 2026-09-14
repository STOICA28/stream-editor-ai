from pydantic_settings import BaseSettings
from pathlib import Path
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"  # Changed for testing without real postgres
    REDIS_URL: str = "redis://localhost:6379/0"
    DATA_DIR: Path = Path("./data")
    MODEL_PROVIDER: str = 'mock'
    LOG_LEVEL: str = 'INFO'
    API_HOST: str = '0.0.0.0'
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = []

    class Config:
        env_file = ".env"

settings = Settings()
