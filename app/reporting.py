from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.frameworks import FRAMEWORK_LABELS, FRAMEWORK_THEMES
from app.models import Control, ControlFramework, ControlStatus, Evidence
from app.scoring import compute_scores

GAP_STATUSES = (ControlStatus.NOT_STARTED, ControlStatus.IN_PROGRESS)


@dataclass
class ReportData:
    generated_at: datetime
    framework: ControlFramework
    framework_label: str
    overall: float
    theme_scores: dict[str, float]
    total_controls: int
    gaps: list[Control]
    stale_items: list[Evidence]


def build_report(db: Session, framework: ControlFramework) -> ReportData:
    controls = db.query(Control).filter(Control.framework == framework).all()
    overall, theme_scores = compute_scores(controls, FRAMEWORK_THEMES[framework])

    gaps = sorted(
        (c for c in controls if c.status in GAP_STATUSES),
        key=lambda c: (GAP_STATUSES.index(c.status), c.id),
    )

    stale_items = sorted(
        (evidence for control in controls for evidence in control.evidence if evidence.is_stale),
        key=lambda e: e.review_due,
    )

    return ReportData(
        generated_at=datetime.now(UTC),
        framework=framework,
        framework_label=FRAMEWORK_LABELS[framework],
        overall=overall,
        theme_scores=theme_scores,
        total_controls=len(controls),
        gaps=gaps,
        stale_items=stale_items,
    )
