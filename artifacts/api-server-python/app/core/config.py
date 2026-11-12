from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required: e.g. postgresql://postgres:pw@localhost:5432/edm_hub
    DATABASE_URL: str
    DEMO_USER_ID: str = "demo-dj"

    # Spotify API credentials (server-side only; integration is currently disabled)
    SPOTIPY_CLIENT_ID: Optional[str] = None
    SPOTIPY_CLIENT_SECRET: Optional[str] = None


settings = Settings()
