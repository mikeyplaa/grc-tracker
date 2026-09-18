import secrets
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "GRC Tracker"
    database_url: str = "sqlite:///./data/grc_tracker.db"

    # Public trust centre branding (surfaces on /trust, which needs no login).
    trust_org_name: str = "Your Organisation"
    trust_contact_email: str = ""

    auth_username: str = "admin"
    auth_password: str = "changeme"
    session_secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))

    @field_validator("session_secret_key")
    @classmethod
    def _non_empty_secret(cls, value: str) -> str:
        # An explicitly empty env var (e.g. an unset docker-compose ${VAR:-})
        # must not override the random default with a weak empty secret.
        return value or secrets.token_hex(32)


@lru_cache
def get_settings() -> Settings:
    return Settings()
