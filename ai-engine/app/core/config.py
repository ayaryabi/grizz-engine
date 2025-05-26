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
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")
    
    # Authentication
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")
    NEXT_PUBLIC_SUPABASE_URL: str = os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
    
    # Monitoring
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

@lru_cache()
def get_settings() -> Settings:
    return Settings() 