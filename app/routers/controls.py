import shutil
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Control, ControlStatus, ControlTheme, Evidence
from app.templating import templates

router = APIRouter(prefix="/controls", tags=["controls"])

EVIDENCE_DIR = Path("data") / "evidence"


def _sort_key(control: Control) -> tuple[int, int]:
    _, section, number = control.id.split(".")
    return int(section), int(number)


def _get_control_or_404(control_id: str, db: Session) -> Control:
    control = db.get(Control, control_id)
    if control is None:
        raise HTTPException(status_code=404, detail="Control not found")
    return control


@router.get("")
def list_controls(request: Request, db: Session = Depends(get_db)):
    controls = sorted(db.query(Control).all(), key=_sort_key)

    grouped: dict[str, list[Control]] = {theme.value: [] for theme in ControlTheme}
    for control in controls:
        grouped[control.theme.value].append(control)
    grouped = {theme: items for theme, items in grouped.items() if items}

    return templates.TemplateResponse(
        request, "controls_list.html", {"grouped": grouped, "total": len(controls)}
    )


@router.get("/{control_id}")
def control_detail(control_id: str, request: Request, db: Session = Depends(get_db)):
    control = _get_control_or_404(control_id, db)
    return templates.TemplateResponse(
        request, "control_detail.html", {"control": control, "statuses": list(ControlStatus)}
    )


@router.post("/{control_id}/status")
def update_status(control_id: str, status: str = Form(...), db: Session = Depends(get_db)):
    control = _get_control_or_404(control_id, db)
    try:
        control.status = ControlStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status") from None
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
    db.commit()
    return RedirectResponse(url=f"/controls/{control_id}", status_code=303)
