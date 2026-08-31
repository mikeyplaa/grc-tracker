from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.db import Base, engine
from app.models import Control, Evidence, ScoreSnapshot  # noqa: F401
from app.routers.controls import router as controls_router
from app.routers.dashboard import router as dashboard_router

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(controls_router)
app.include_router(dashboard_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/controls")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
