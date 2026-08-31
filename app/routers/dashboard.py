from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.frameworks import FRAMEWORK_LABELS, FRAMEWORK_SLUGS, FRAMEWORK_THEMES, framework_from_slug
from app.models import Control, ScoreSnapshot
from app.reporting import build_report
from app.scoring import compute_scores
from app.templating import templates

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _framework_tabs(active_slug: str) -> list[dict]:
    return [
        {"slug": slug, "label": FRAMEWORK_LABELS[framework], "active": slug == active_slug}
        for framework, slug in FRAMEWORK_SLUGS.items()
    ]


@router.get("")
def dashboard(request: Request, framework: str = "iso27001", db: Session = Depends(get_db)):
    selected = framework_from_slug(framework)
    report = build_report(db, selected)
    snapshots = (
        db.query(ScoreSnapshot)
        .filter(ScoreSnapshot.framework == selected)
        .order_by(ScoreSnapshot.taken_at)
        .all()
    )

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
            "framework_label": report.framework_label,
            "framework_slug": framework,
            "framework_tabs": _framework_tabs(framework),
        },
    )


@router.post("/snapshot")
def take_snapshot(framework: str = "iso27001", db: Session = Depends(get_db)):
    selected = framework_from_slug(framework)
    controls = db.query(Control).filter(Control.framework == selected).all()
    overall, theme_scores = compute_scores(controls, FRAMEWORK_THEMES[selected])
    db.add(ScoreSnapshot(framework=selected, overall_score=overall, theme_scores=theme_scores))
    db.commit()
    return RedirectResponse(url=f"/dashboard?framework={framework}", status_code=303)
