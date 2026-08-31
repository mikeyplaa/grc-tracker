import re
from pathlib import Path

from app.models import ControlFramework

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FRAMEWORK_LABELS: dict[ControlFramework, str] = {
    ControlFramework.ISO_27001_2022: "ISO 27001:2022",
    ControlFramework.SOC_2: "SOC 2",
}

FRAMEWORK_SLUGS: dict[ControlFramework, str] = {
    ControlFramework.ISO_27001_2022: "iso27001",
    ControlFramework.SOC_2: "soc2",
}
SLUG_TO_FRAMEWORK: dict[str, ControlFramework] = {
    slug: framework for framework, slug in FRAMEWORK_SLUGS.items()
}
DEFAULT_FRAMEWORK = ControlFramework.ISO_27001_2022

# Display order for each framework's theme/category groupings.
FRAMEWORK_THEMES: dict[ControlFramework, list[str]] = {
    ControlFramework.ISO_27001_2022: [
        "Organizational",
        "People",
        "Physical",
        "Technological",
    ],
    ControlFramework.SOC_2: [
        "Security",
        "Availability",
        "Confidentiality",
        "Processing Integrity",
    ],
}

FRAMEWORK_SEED_FILES: dict[ControlFramework, Path] = {
    ControlFramework.ISO_27001_2022: DATA_DIR / "iso27001_2022_annex_a.json",
    ControlFramework.SOC_2: DATA_DIR / "soc2_2017_tsc.json",
}


def framework_from_slug(slug: str) -> ControlFramework:
    return SLUG_TO_FRAMEWORK.get(slug, DEFAULT_FRAMEWORK)


def natural_sort_key(control_id: str) -> tuple:
    """Sorts alphanumeric IDs (e.g. "A.5.9" < "A.5.10", "CC1.1" < "CC1.2") by
    splitting into text/number runs and comparing numbers numerically."""
    return tuple(
        int(part) if part.isdigit() else part
        for part in re.split(r"(\d+)", control_id)
    )
