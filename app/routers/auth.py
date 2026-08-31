from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from app.auth import SESSION_KEY, safe_next_path, verify_credentials
from app.templating import templates

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request, next: str = "/controls"):
    return templates.TemplateResponse(
        request, "login.html", {"next": safe_next_path(next), "error": None}
    )


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/controls"),
):
    next_path = safe_next_path(next)
    if verify_credentials(username, password):
        request.session[SESSION_KEY] = True
        return RedirectResponse(url=next_path, status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        {"next": next_path, "error": "Invalid username or password."},
        status_code=401,
    )


@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
