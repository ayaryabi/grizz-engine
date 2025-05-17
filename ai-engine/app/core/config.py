from functools import lru_cache

class Settings:
    PROJECT_NAME: str = "Grizz Chat"
    VERSION: str = "0.1.0"

@lru_cache()
def get_settings() -> Settings:
    return Settings() 