from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Control, ScoreSnapshot
from app.reporting import build_report
from app.scoring import compute_scores
from app.templating import templates

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(request: Request, db: Session = Depends(get_db)):
    report = build_report(db)
    snapshots = db.query(ScoreSnapshot).order_by(ScoreSnapshot.taken_at).all()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "overall": report.overall,
            "total_controls": report.total_controls,
            "theme_scores": report.theme_scores,
            "gaps": report.gaps,
            "stale_items": report.stale_items,
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
