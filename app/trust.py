"""Domain logic for the public trust centre.

Everything the unauthenticated ``/trust`` surface renders goes through this
module. Controls are mapped to :class:`PublicControl` first, which carries only
the fields that are safe to publish -- ``owner_note`` and the evidence
titles/locations have no representation here at all, so a template edit cannot
accidentally leak them.
"""
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.frameworks import (
    FRAMEWORK_LABELS,
    FRAMEWORK_SLUGS,
    FRAMEWORK_THEMES,
    natural_sort_key,
)
from app.models import Control, ControlFramework, ControlStatus
from app.scoring import compute_scores


@dataclass(frozen=True)
class PublicControl:
    """A control as the outside world sees it."""

    id: str
    framework_label: str
    framework_slug: str
    theme: str
    title: str
    description: str
    status: ControlStatus
    last_reviewed: date | None
    evidence_count: int
    evidence_last_refreshed: datetime | None
    has_stale_evidence: bool


@dataclass
class TrustView:
    framework: ControlFramework
    framework_label: str
    framework_slug: str
    overall: float
    theme_scores: dict[str, float]
    grouped: dict[str, list[PublicControl]]
    total_published: int
    last_updated: datetime | None


def _to_public(control: Control) -> PublicControl:
    return PublicControl(
        id=control.id,
        framework_label=FRAMEWORK_LABELS[control.framework],
        framework_slug=FRAMEWORK_SLUGS[control.framework],
        theme=control.theme,
        title=control.title,
        description=control.description,
        status=control.status,
        last_reviewed=control.last_reviewed,
        evidence_count=len(control.evidence),
        evidence_last_refreshed=control.evidence_last_refreshed,
        has_stale_evidence=control.has_stale_evidence,
    )


def published_controls(db: Session, framework: ControlFramework) -> list[Control]:
    controls = (
        db.query(Control)
        .filter(Control.framework == framework, Control.is_public.is_(True))
        .all()
    )
    return sorted(controls, key=lambda c: natural_sort_key(c.id))


def published_frameworks(db: Session) -> list[ControlFramework]:
    """Frameworks with at least one published control, in the app's usual order.

    Framework visibility is derived rather than separately toggled: a framework
    appears on the trust centre exactly when something inside it is published,
    so there is one publishing switch to reason about, not two.
    """
    rows = (
        db.query(Control.framework)
        .filter(Control.is_public.is_(True))
        .distinct()
        .all()
    )
    present = {row[0] for row in rows}
    return [framework for framework in FRAMEWORK_SLUGS if framework in present]


def build_trust_view(db: Session, framework: ControlFramework) -> TrustView:
    controls = published_controls(db, framework)

    # Score over published controls only, and only over themes that actually
    # have published controls -- the public number must never be a function of
    # anything unpublished.
    themes_present = [
        theme for theme in FRAMEWORK_THEMES[framework] if any(c.theme == theme for c in controls)
    ]
    for control in controls:
        if control.theme not in themes_present:
            themes_present.append(control.theme)

    overall, theme_scores = compute_scores(controls, themes_present)

    grouped: dict[str, list[PublicControl]] = {theme: [] for theme in themes_present}
    for control in controls:
        grouped[control.theme].append(_to_public(control))

    published_dates = [c.published_at for c in controls if c.published_at is not None]

    return TrustView(
        framework=framework,
        framework_label=FRAMEWORK_LABELS[framework],
        framework_slug=FRAMEWORK_SLUGS[framework],
        overall=overall,
        theme_scores=theme_scores,
        grouped=grouped,
        total_published=len(controls),
        last_updated=max(published_dates) if published_dates else None,
    )


def public_control_or_none(db: Session, control_id: str) -> PublicControl | None:
    """Look up a single published control. Unpublished and unknown IDs are
    indistinguishable to the caller, so the trust centre cannot be used to probe
    which control IDs exist but are being held back."""
    control = db.get(Control, control_id)
    if control is None or not control.is_public:
        return None
    return _to_public(control)
