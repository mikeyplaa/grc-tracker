# Next Steps

## Phase 0 — Scaffold
- [x] Repo structure: `/app` (FastAPI), `/data` (seed JSON), `/docker`
- [x] docker-compose with app + SQLite volume
- [x] Basic FastAPI app boots, health check route

## Phase 1 — Controls (read-only)
- [x] Control + Evidence + ScoreSnapshot models (SQLAlchemy)
- [ ] Seed script loading ISO 27001:2022 Annex A controls into DB
- [ ] List/detail view of controls, grouped by theme

## Phase 2 — Evidence + status updates
- [ ] Update control status (UI + endpoint)
- [ ] Attach evidence to a control (file upload or link), set review-due date
- [ ] Stale-evidence detection logic

## Phase 3 — Scoring + dashboard
- [ ] Scoring calculation (overall + by theme)
- [ ] Snapshot-on-demand (or scheduled) to populate ScoreSnapshot history
- [ ] Dashboard: overall score, theme breakdown chart, trend line, gaps list

## Phase 4 — Export + polish
- [ ] Markdown/PDF summary export
- [ ] Basic styling pass — this doubles as a portfolio piece, so make it look sharp
- [ ] Deploy to Proxmox lab via docker-compose

## Phase 5 — Stretch (post-MVP)
- [ ] Second framework support (SOC 2?) using the same control/evidence model
- [ ] Simple auth (single local login) if exposing beyond the lab network
- [ ] Manual "connector" style checklist prompts (poor-man's automated evidence)

---
*Update this file at the end of each Claude Code session: tick off what's done, note
any decisions or deviations from the plan, and adjust upcoming phases as needed.*

## Session notes
- Phase 0 complete: FastAPI app scaffolded under `app/`, with `app/main.py` exposing
  `GET /health` returning `{"status": "ok"}`. Config via `pydantic-settings`
  (`app/core/config.py`), defaulting to a SQLite file at `data/grc_tracker.db`.
- `docker-compose.yml` + `docker/Dockerfile` build the app and mount `./data` as a
  volume for the SQLite file. Run with `docker compose up --build`.
- Local run without Docker: `pip install -r requirements.txt && uvicorn app.main:app --reload`.
- Verified `/health` returns 200 locally (see below).
- Phase 1 models complete: `app/db.py` sets up the SQLAlchemy engine/session
  (`SessionLocal`, `get_db` dependency) and declarative `Base`. Models live under
  `app/models/`: `Control` (theme/status enums, `owner_note`, `last_reviewed`),
  `Evidence` (FK to `Control`, `uploaded_at` server-default timestamp, `review_due`),
  and `ScoreSnapshot` (`overall_score` float, `theme_scores` JSON dict).
  `app/main.py` creates tables on startup via `Base.metadata.create_all` — no
  migrations tool yet (SQLite, single-user, MVP); revisit with Alembic if the
  schema needs versioned migrations later.
- Verified with a TestClient round-trip: inserted a Control + linked Evidence +
  a ScoreSnapshot, confirmed the relationship and JSON column read back correctly.
- Next up: seed script loading the ISO 27001:2022 Annex A controls, then the
  read-only list/detail view grouped by theme.
