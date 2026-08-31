from app.models import Control, ControlStatus, ControlTheme

STATUS_ORDER = [
    ControlStatus.NOT_STARTED,
    ControlStatus.IN_PROGRESS,
    ControlStatus.IMPLEMENTED,
    ControlStatus.EVIDENCED,
]

STATUS_WEIGHT = {
    ControlStatus.NOT_STARTED: 0.0,
    ControlStatus.IN_PROGRESS: 0.33,
    ControlStatus.IMPLEMENTED: 0.66,
    ControlStatus.EVIDENCED: 1.0,
}


def effective_score(control: Control) -> float:
    """Weighted status score, dropped one tier if the control has stale evidence."""
    index = STATUS_ORDER.index(control.status)
    if control.has_stale_evidence and index > 0:
        index -= 1
    return STATUS_WEIGHT[STATUS_ORDER[index]]


def compute_scores(controls: list[Control]) -> tuple[float, dict[str, float]]:
    """Returns (overall_score, {theme: score}), each a 0..1 mean of effective_score."""
    theme_totals: dict[str, list[float]] = {theme.value: [] for theme in ControlTheme}
    for control in controls:
        theme_totals[control.theme.value].append(effective_score(control))

    theme_scores = {
        theme: (sum(scores) / len(scores) if scores else 0.0)
        for theme, scores in theme_totals.items()
    }

    overall = sum(effective_score(c) for c in controls) / len(controls) if controls else 0.0
    return overall, theme_scores
