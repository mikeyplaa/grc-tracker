from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.db import Base, engine
from app.models import Control, Evidence, ScoreSnapshot  # noqa: F401
from app.routers.controls import router as controls_router
from app.routers.dashboard import router as dashboard_router
from app.routers.export import router as export_router
from app.seed import seed_controls

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static"
)
app.include_router(controls_router)
app.include_router(dashboard_router)
app.include_router(export_router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_controls()


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/controls")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
