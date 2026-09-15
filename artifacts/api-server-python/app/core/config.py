import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/edmhub")
    DEMO_USER_ID: str = "demo-dj"
    API_V1_STR: str = "/api"

settings = Settings()
