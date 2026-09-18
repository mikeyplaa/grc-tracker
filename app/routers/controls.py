import shutil
from datetime import UTC, date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.frameworks import (
    FRAMEWORK_LABELS,
    FRAMEWORK_SLUGS,
    FRAMEWORK_THEMES,
    framework_from_slug,
    natural_sort_key,
)
from app.models import Control, ControlStatus, Evidence
from app.templating import templates

router = APIRouter(prefix="/controls", tags=["controls"])

EVIDENCE_DIR = Path("data") / "evidence"


def _now() -> datetime:
    """Naive UTC, matching the DateTime columns elsewhere in the schema."""
    return datetime.now(UTC).replace(tzinfo=None)


def _touch_public_record(control: Control) -> None:
    """Keep the trust centre's 'last updated' honest: any admin change to a
    published control is a change to what the public sees."""
    if control.is_public:
        control.published_at = _now()


def _get_control_or_404(control_id: str, db: Session) -> Control:
    control = db.get(Control, control_id)
    if control is None:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


def _framework_tabs(active_slug: str) -> list[dict]:
    return [
        {"slug": slug, "label": FRAMEWORK_LABELS[framework], "active": slug == active_slug}
        for framework, slug in FRAMEWORK_SLUGS.items()
    ]


@router.get("")
def list_controls(request: Request, framework: str = "iso27001", db: Session = Depends(get_db)):
    selected = framework_from_slug(framework)
    controls = sorted(
        db.query(Control).filter(Control.framework == selected).all(),
        key=lambda c: natural_sort_key(c.id),
    )

    grouped: dict[str, list[Control]] = {theme: [] for theme in FRAMEWORK_THEMES[selected]}
    for control in controls:
        grouped.setdefault(control.theme, []).append(control)
    grouped = {theme: items for theme, items in grouped.items() if items}

    return templates.TemplateResponse(
        request,
        "controls_list.html",
        {
            "grouped": grouped,
            "total": len(controls),
            "published_count": sum(1 for c in controls if c.is_public),
            "framework_label": FRAMEWORK_LABELS[selected],
            "framework_tabs": _framework_tabs(framework),
        },
    )


@router.get("/{control_id}")
def control_detail(control_id: str, request: Request, db: Session = Depends(get_db)):
    control = _get_control_or_404(control_id, db)
    return templates.TemplateResponse(
        request,
        "control_detail.html",
        {
            "control": control,
            "statuses": list(ControlStatus),
            "framework_slug": FRAMEWORK_SLUGS[control.framework],
        },
    )


@router.post("/{control_id}/status")
def update_status(control_id: str, status: str = Form(...), db: Session = Depends(get_db)):
    control = _get_control_or_404(control_id, db)
    try:
        control.status = ControlStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status") from None
    _touch_public_record(control)
    db.commit()
    return RedirectResponse(url=f"/controls/{control_id}", status_code=303)


@router.post("/{control_id}/publish")
def set_published(control_id: str, publish: bool = Form(...), db: Session = Depends(get_db)):
    """Toggle whether this control appears on the public trust centre.

    Publishing is per-control and explicit -- there is no bulk or implicit
    publish anywhere in the app, so nothing reaches /trust by accident.
    """
    control = _get_control_or_404(control_id, db)
    control.is_public = publish
    control.published_at = _now() if publish else None
    db.commit()
    return RedirectResponse(url=f"/controls/{control_id}", status_code=303)


@router.post("/{control_id}/evidence")
def add_evidence(
    control_id: str,
    title: str = Form(...),
    url: str = Form(""),
    review_due: date | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    control = _get_control_or_404(control_id, db)

    url = url.strip()
    if file is not None and file.filename:
        EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename).name
        dest = EVIDENCE_DIR / f"{control_id}_{safe_name}"
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        location = str(dest)
    elif url:
        location = url
    else:
        raise HTTPException(status_code=400, detail="Provide a file or a URL")

    db.add(
        Evidence(
            control_id=control_id,
            title=title,
            file_path_or_url=location,
            review_due=review_due,
        )
    )
    _touch_public_record(control)
    db.commit()
    return RedirectResponse(url=f"/controls/{control_id}", status_code=303)
