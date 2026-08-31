import secrets

from fastapi import HTTPException, Request

from app.core.config import get_settings

SESSION_KEY = "authenticated"


def is_authenticated(request: Request) -> bool:
    return bool(request.session.get(SESSION_KEY))


def require_login(request: Request) -> None:
    if not is_authenticated(request):
        raise HTTPException(
            status_code=303,
            headers={"Location": f"/login?next={request.url.path}"},
        )


def verify_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    username_ok = secrets.compare_digest(username, settings.auth_username)
    password_ok = secrets.compare_digest(password, settings.auth_password)
    return username_ok and password_ok


def safe_next_path(next_path: str) -> str:
    if next_path.startswith("/") and not next_path.startswith("//"):
        return next_path
    return "/controls"
