import json

from app.db import Base, SessionLocal, engine
from app.frameworks import FRAMEWORK_SEED_FILES
from app.models import Control


def seed_controls() -> None:
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        total_added, total_skipped = 0, 0
        for framework, seed_file in FRAMEWORK_SEED_FILES.items():
            entries = json.loads(seed_file.read_text())
            for entry in entries:
                if db.get(Control, entry["id"]) is not None:
                    total_skipped += 1
                    continue
                db.add(
                    Control(
                        id=entry["id"],
                        framework=framework,
                        theme=entry["theme"],
                        title=entry["title"],
                        description=entry["description"],
                    )
                )
                total_added += 1
        db.commit()
        print(f"Seeded {total_added} controls, skipped {total_skipped} already present.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_controls()
