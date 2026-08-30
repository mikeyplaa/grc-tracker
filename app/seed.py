import json
from pathlib import Path

from app.db import Base, SessionLocal, engine
from app.models import Control, ControlTheme

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "iso27001_2022_annex_a.json"


def seed_controls() -> None:
    Base.metadata.create_all(bind=engine)
    controls = json.loads(SEED_FILE.read_text())

    db = SessionLocal()
    try:
        added, skipped = 0, 0
        for entry in controls:
            if db.get(Control, entry["id"]) is not None:
                skipped += 1
                continue
            db.add(
                Control(
                    id=entry["id"],
                    theme=ControlTheme(entry["theme"]),
                    title=entry["title"],
                    description=entry["description"],
                )
            )
            added += 1
        db.commit()
        print(f"Seeded {added} controls, skipped {skipped} already present.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_controls()
