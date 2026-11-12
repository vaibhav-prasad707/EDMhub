from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required: e.g. postgresql://postgres:pw@localhost:5432/edm_hub
    DATABASE_URL: str

    # Auth: sign session cookies with this secret (use a long random string).
    #   python -c "import secrets; print(secrets.token_urlsafe(48))"
    JWT_SECRET: str = Field(min_length=32)
    SESSION_HOURS: int = 24 * 7
    # Set to true when served over HTTPS (production).
    COOKIE_SECURE: bool = False

    # Spotify API credentials (server-side only; integration is currently disabled)
    SPOTIPY_CLIENT_ID: Optional[str] = None
    SPOTIPY_CLIENT_SECRET: Optional[str] = None


settings = Settings()
