from fastapi import FastAPI

from app.core.config import get_settings
from app.db import Base, engine
from app.models import Control, Evidence, ScoreSnapshot  # noqa: F401

settings = get_settings()

app = FastAPI(title=settings.app_name)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
