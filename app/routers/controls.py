from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Control, ControlTheme
from app.templating import templates

router = APIRouter(prefix="/controls", tags=["controls"])


def _sort_key(control: Control) -> tuple[int, int]:
    _, section, number = control.id.split(".")
    return int(section), int(number)


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
    control = db.get(Control, control_id)
    if control is None:
        raise HTTPException(status_code=404, detail="Control not found")

    return templates.TemplateResponse(request, "control_detail.html", {"control": control})
