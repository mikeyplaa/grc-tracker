import logging
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.auth import require_login
from app.core.config import get_settings
from app.db import Base, engine
from app.models import Control, Evidence, ScoreSnapshot  # noqa: F401
from app.routers.auth import router as auth_router
from app.routers.controls import router as controls_router
from app.routers.dashboard import router as dashboard_router
from app.routers.export import router as export_router
from app.seed import seed_controls

logger = logging.getLogger("grc_tracker")

settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret_key,
    session_cookie="grc_session",
    max_age=60 * 60 * 24 * 14,
)
app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static"
)
app.include_router(auth_router)
app.include_router(controls_router, dependencies=[Depends(require_login)])
app.include_router(dashboard_router, dependencies=[Depends(require_login)])
app.include_router(export_router, dependencies=[Depends(require_login)])


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    seed_controls()
    if settings.auth_password == "changeme":
        logger.warning(
            "AUTH_PASSWORD is unset and using the default 'changeme'. "
            "Set AUTH_USERNAME/AUTH_PASSWORD in your environment before "
            "exposing this app beyond localhost."
        )


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/controls")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
