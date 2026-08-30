from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "GRC Tracker"
    database_url: str = "sqlite:///./data/grc_tracker.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
