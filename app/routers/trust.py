"""Public, unauthenticated trust centre routes.

This router is deliberately mounted WITHOUT the ``require_login`` dependency
that guards the admin routers in ``app.main``. Every response it renders is
built from :mod:`app.trust`, which only exposes published controls.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db
from app.frameworks import FRAMEWORK_LABELS, FRAMEWORK_SLUGS, framework_from_slug
from app.models import ControlFramework
from app.templating import templates
from app.trust import build_trust_view, public_control_or_none, published_frameworks

router = APIRouter(prefix="/trust", tags=["trust"])


def _branding() -> dict[str, str]:
    settings = get_settings()
    return {
        "org_name": settings.trust_org_name,
        "contact_email": settings.trust_contact_email,
    }


def _tabs(visible: list[ControlFramework], active_slug: str) -> list[dict]:
    return [
        {
            "slug": FRAMEWORK_SLUGS[framework],
            "label": FRAMEWORK_LABELS[framework],
            "active": FRAMEWORK_SLUGS[framework] == active_slug,
        }
        for framework in visible
    ]


@router.get("")
def trust_centre(request: Request, framework: str | None = None, db: Session = Depends(get_db)):
    visible = published_frameworks(db)
    if not visible:
        return templates.TemplateResponse(
            request,
            "trust_empty.html",
            {**_branding()},
        )

    # Default to the first framework that actually has published controls, so
    # the landing page is never an empty tab.
    selected = framework_from_slug(framework) if framework else visible[0]
    if selected not in visible:
        selected = visible[0]

    view = build_trust_view(db, selected)
    return templates.TemplateResponse(
        request,
        "trust_index.html",
        {
            **_branding(),
            "view": view,
            "framework_tabs": _tabs(visible, view.framework_slug),
        },
    )


@router.get("/controls/{control_id}")
def trust_control_detail(control_id: str, request: Request, db: Session = Depends(get_db)):
    control = public_control_or_none(db, control_id)
    if control is None:
        # Same 404 for "no such control" and "not published" -- see
        # app.trust.public_control_or_none.
        raise HTTPException(status_code=404, detail="Control not found")

    return templates.TemplateResponse(
        request,
        "trust_control.html",
        {**_branding(), "control": control},
    )
