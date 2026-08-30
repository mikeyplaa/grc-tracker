# Next Steps

## Phase 0 — Scaffold
- [x] Repo structure: `/app` (FastAPI), `/data` (seed JSON), `/docker`
- [x] docker-compose with app + SQLite volume
- [x] Basic FastAPI app boots, health check route

## Phase 1 — Controls (read-only)
- [x] Control + Evidence + ScoreSnapshot models (SQLAlchemy)
- [x] Seed script loading ISO 27001:2022 Annex A controls into DB
- [x] List/detail view of controls, grouped by theme

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
- Seed script complete: `data/iso27001_2022_annex_a.json` holds all 93 ISO
  27001:2022 Annex A controls (37 Organizational, 8 People, 14 Physical,
  34 Technological — verified counts and sequential numbering programmatically).
  `app/seed.py` (`python -m app.seed`) upserts them into the `controls` table,
  skipping any `id` already present, so it's safe to re-run.
  **Flag for Mike**: the `id`/`theme`/`title` fields are the official Annex A
  reference labels (widely published, high confidence). The `description`
  field is a short paraphrase in my own words, not the verbatim ISO standard
  text — I don't have the copyrighted control wording memorized reliably
  enough to reproduce it exactly, and reproducing it verbatim would raise
  copyright concerns anyway. If you want exact wording for the portfolio
  artifact, swap in text from your licensed copy of the standard; the schema
  doesn't care which you use.
- Phase 1 complete: added server-rendered Jinja2 views. `app/templating.py`
  holds the shared `Jinja2Templates` instance; `app/routers/controls.py`
  serves `GET /controls` (all controls grouped by theme, in Annex A order,
  numerically sorted within each theme — e.g. A.5.9 before A.5.10) and
  `GET /controls/{id}` (detail page with status badge, description, owner
  note, last-reviewed date, and any attached evidence — 404s on unknown ids).
  `GET /` redirects to `/controls`. Kept styling to a single inline `<style>`
  block in `app/templates/base.html` rather than a static-files mount; the
  real styling pass is scheduled for Phase 4 per the plan.
  Verified by booting the app, seeding, and curling `/`, `/controls`,
  `/controls/A.5.1`, and a 404 case — all correct; also checked the rendered
  HTML groups controls into the right theme counts (37/8/14/34) and sorts
  numerically within each theme.
- Phase 1 is now fully complete. Next up: Phase 2 — update control status
  (UI + endpoint), attach evidence to a control (file upload or link) with a
  review-due date, and stale-evidence detection logic.
