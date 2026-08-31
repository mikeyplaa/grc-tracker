from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Control, ControlStatus, ControlTheme, ScoreSnapshot
from app.scoring import compute_scores
from app.templating import templates

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

GAP_STATUSES = (ControlStatus.NOT_STARTED, ControlStatus.IN_PROGRESS)


@router.get("")
def dashboard(request: Request, db: Session = Depends(get_db)):
    controls = db.query(Control).all()
    overall, theme_scores = compute_scores(controls)
    theme_scores_ordered = {theme.value: theme_scores[theme.value] for theme in ControlTheme}

    gaps = sorted(
        (c for c in controls if c.status in GAP_STATUSES),
        key=lambda c: (GAP_STATUSES.index(c.status), c.id),
    )

    stale_items = sorted(
        (evidence for control in controls for evidence in control.evidence if evidence.is_stale),
        key=lambda e: e.review_due,
    )

    snapshots = db.query(ScoreSnapshot).order_by(ScoreSnapshot.taken_at).all()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "overall": overall,
            "total_controls": len(controls),
            "theme_scores": theme_scores_ordered,
            "gaps": gaps,
            "stale_items": stale_items,
            "snapshots": snapshots,
        },
    )


@router.post("/snapshot")
def take_snapshot(db: Session = Depends(get_db)):
    controls = db.query(Control).all()
    overall, theme_scores = compute_scores(controls)
    db.add(ScoreSnapshot(overall_score=overall, theme_scores=theme_scores))
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)
