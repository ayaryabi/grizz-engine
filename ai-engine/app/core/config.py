from functools import lru_cache
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseModel):
    PROJECT_NAME: str = "Grizz Chat"
    VERSION: str = "0.1.0"
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./grizz_chat.db")
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")

@lru_cache()
def get_settings() -> Settings:
    return Settings() 