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
- [x] Update control status (UI + endpoint)
- [x] Attach evidence to a control (file upload or link), set review-due date
- [x] Stale-evidence detection logic

## Phase 3 — Scoring + dashboard
- [x] Scoring calculation (overall + by theme)
- [x] Snapshot-on-demand (or scheduled) to populate ScoreSnapshot history
- [x] Dashboard: overall score, theme breakdown chart, trend line, gaps list

## Phase 4 — Export + polish
- [x] Markdown/PDF summary export
- [x] Basic styling pass — this doubles as a portfolio piece, so make it look sharp
- [ ] Deploy to Proxmox lab via docker-compose (needs Mike's lab access — see notes)

## Phase 5 — Stretch (post-MVP)
- [ ] Second framework support (deferred — Mike wants to specify which framework separately)
- [x] Simple auth (single local login) if exposing beyond the lab network
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
- Phase 1 is now fully complete.
- Phase 2 complete:
  - `POST /controls/{id}/status` updates a control's status from a `<select>`
    on the detail page (redirects back to the detail page, 303).
  - `POST /controls/{id}/evidence` attaches evidence via either a link (`url`
    form field) or a file upload, plus an optional `review_due` date. Uploaded
    files are saved under `data/evidence/{control_id}_{filename}` (filename
    sanitized to its basename to avoid path traversal); this directory rides
    along in the same `./data` Docker volume as the SQLite file, so it
    persists across container restarts. Requires exactly one of file/url —
    400s if neither is given. Added `python-multipart` to requirements.txt
    (required by FastAPI for form/file parsing).
  - Stale-evidence detection: `Evidence.is_stale` (review_due in the past)
    and `Control.has_stale_evidence` (any stale evidence) are plain Python
    properties, not DB columns — cheap to compute at this scale (93 controls,
    a handful of evidence items each), no need for a query-level flag yet.
    Surfaced in the UI as a "Stale" badge on the evidence row and a "Stale
    evidence" badge next to the control's status.
  - `data/evidence/` is gitignored (uploaded files are user data, like the
    SQLite db).
  - Verified end-to-end: status update via curl, evidence-by-link with a
    past review_due (renders as stale), evidence-by-file-upload with a
    future review_due (renders as fresh), and the 400 case with neither
    file nor url provided.
- Phase 2 is now fully complete.
- Phase 3 complete:
  - `app/scoring.py`: `effective_score(control)` maps status to the weights
    from CLAUDE.md (Not Started=0, In Progress=0.33, Implemented=0.66,
    Evidenced=1.0), dropping one tier if `control.has_stale_evidence` is
    true (stale evidence pulls the effective score down, per the brief).
    `compute_scores(controls)` returns `(overall, {theme: score})`, each a
    plain mean of effective scores (0..1).
  - `POST /dashboard/snapshot`: computes current scores and inserts a
    `ScoreSnapshot` row (on-demand, no scheduler — fits the single-user
    home-lab use case; a cron/scheduled option is easy to bolt on later
    if wanted).
  - `GET /dashboard`: overall score (big number), a theme-breakdown bar
    chart, a score-over-time trend line (hidden with an empty-state message
    until at least one snapshot exists), a gaps list (Not Started/In
    Progress controls, most-urgent-first), and a stale-evidence list sorted
    by how overdue the review is. Added "Controls / Dashboard" nav in the
    header.
  - Charts use Chart.js (matches CLAUDE.md's "Chart.js or similar, kept
    lightweight" suggestion); see Phase 4 notes below — ended up vendoring
    it locally rather than loading from a CDN.
  - Added a `tojson` Jinja filter (`app/templating.py`) since plain Jinja2
    (unlike Flask) doesn't ship one; wrapped its output in `markupsafe.Markup`
    so the JSON isn't HTML-escaped inside `<script>` tags — caught this by
    inspecting the rendered page (autoescaping turned `"` into `&#34;`,
    which would have broken the chart JS in a real browser). Added
    `markupsafe` to requirements.txt as an explicit dependency since we
    import it directly.
  - Verified end-to-end: seeded 93 controls, set a few statuses, confirmed
    the computed overall/theme scores match hand-calculated values, took a
    snapshot, and confirmed the rendered chart data (`themeLabels`,
    `themeData`, `trendLabels`, `trendData`) is valid unescaped JSON with
    the right numbers.
- Phase 3 is now fully complete — this closes out the MVP core loop (Framework
  → Control record → Evidence → Scoring → Dashboard) from CLAUDE.md.
- Phase 4 (export + styling) complete; deployment to the actual Proxmox lab
  is not (see below — needs Mike's lab access, which this session doesn't have).
  - **Export**: `app/reporting.py` factors the shared "gather dashboard data"
    logic (`build_report(db)`) out of `dashboard.py` so both the dashboard and
    the new export routes use one source of truth. `app/routers/export.py`
    adds `GET /export/markdown` (plain-text summary, `Content-Disposition:
    attachment`) and `GET /export/pdf` (same content via `fpdf2`). Added
    `fpdf2` to requirements.txt — flagging this as a new dependency per the
    working agreement: chose it because it's pure-Python with no system-level
    deps (unlike e.g. WeasyPrint, which needs Cairo/Pango and would complicate
    the Docker image). Hit and fixed a real bug while building this: fpdf2's
    `multi_cell()` leaves the cursor at the right margin by default, so a
    second call computed negative available width and threw
    `FPDFException: Not enough horizontal space` — fixed by passing
    `new_x="LMARGIN", new_y="NEXT"` explicitly, same as the `cell()` calls.
    Sent Mike sample `.md`/`.pdf` output to review.
  - **Styling pass**: dark theme polish — shield emoji favicon, a
    Controls/Dashboard nav with active-state highlighting, a footer, subtle
    panel shadows, and export buttons on the dashboard. Verified visually
    with Playwright screenshots of `/controls`, `/controls/A.5.1`, and
    `/dashboard` (not just curl/HTTP-status checks) since this is a UI change.
  - **Chart.js delivery change**: the dashboard originally loaded Chart.js
    from the jsdelivr CDN (Phase 3). Screenshotting the dashboard surfaced
    that the charts were blank — this sandbox's network policy blocks that
    CDN outright, and more importantly, relying on an external CDN is a real
    fragility for a tool meant to run on a segmented home-lab network where
    a browser might not have general internet egress. Vendored Chart.js
    instead: fetched `chart.js@4.4.4`'s UMD build via npm (registry.npmjs.org
    was reachable), copied it to `app/static/vendor/chart.umd.js` (MIT
    license file alongside it), mounted `/static` via FastAPI's
    `StaticFiles`, and pointed the dashboard's `<script>` tag at the local
    copy. Re-verified with Playwright: no console/page errors, both charts
    render. No new Python dependency — just a vendored static asset.
  - **Auto-seed on startup**: since `seed_controls()` is idempotent
    (upserts, skips existing ids), wired it into the FastAPI startup event
    alongside `Base.metadata.create_all`. A fresh deploy now has all 93
    controls immediately — no manual `python -m app.seed` step needed on
    first boot, and it's a safe no-op on every restart after that.
  - **Deployment to Proxmox — not done, and here's exactly why**: this
    session has no access to Mike's actual Proxmox host, and this sandbox
    has no Docker daemon available either (`docker version` connects fine
    but `no such file or directory` on the daemon socket), so `docker build`
    / `docker compose up` were never literally run here. What *is* verified:
    the app boots and behaves correctly under the same install command
    (`pip install -r requirements.txt`) and run command
    (`uvicorn app.main:app`) the Dockerfile uses, and `docker/Dockerfile`'s
    `COPY app ./app` correctly picks up the new `app/static/` directory (no
    Dockerfile changes were needed). To actually deploy: on the Proxmox host,
    clone the repo and run `docker compose up --build -d`, then confirm
    `/health` and `/dashboard` respond. Leaving the NEXT_STEPS checkbox
    unticked until that's actually been run on real hardware.
- MVP scope (Phases 0–4) is functionally complete pending that one real
  deployment step. Phase 5 (stretch, post-MVP) remains optional: second
  framework support, simple auth, manual "connector" checklists — none of
  it blocks calling this a working v1.
- **Phase 5 — simple auth complete.** Asked Mike which Phase 5 items to
  build (per CLAUDE.md's "ask before adding an auth layer") and which auth
  mechanism; he chose a login form + session cookie over HTTP Basic, and
  deferred the second-framework item to specify separately later.
  - `app/auth.py`: `require_login` dependency (redirects to
    `/login?next=<path>` via a 303 + `Location` header on `HTTPException`
    — no custom exception handler needed, FastAPI's default one forwards
    the header and browsers follow the redirect regardless of body).
    `verify_credentials` uses `secrets.compare_digest` for constant-time
    comparison. `safe_next_path` rejects protocol-relative (`//host/...`)
    values to close an open-redirect path through the `next` param.
  - `app/routers/auth.py` + `app/templates/login.html`: `GET/POST /login`,
    `GET /logout`. Wrong credentials re-render the form with a 401 and an
    error message rather than redirecting.
  - `app/core/config.py`: added `auth_username`/`auth_password` (env vars,
    default `admin`/`changeme`) and `session_secret_key` (random via
    `secrets.token_hex(32)` if unset). Added a `field_validator` so an env
    var explicitly set to `""` (e.g. an unset `${SESSION_SECRET_KEY:-}` in
    docker-compose) still falls back to a random secret instead of signing
    sessions with an empty key — caught this by tracing through what
    `docker compose config` actually resolves, not just the happy path.
  - `SessionMiddleware` (from `starlette.middleware.sessions`, needs
    `itsdangerous` — added to requirements.txt) wraps the app; a 14-day
    session cookie (`grc_session`). `require_login` is applied via
    `dependencies=[Depends(require_login)]` on `app.include_router(...)`
    for the controls/dashboard/export routers, so no individual route
    needed editing. `/health`, `/login`, `/static/*` stay public
    (container healthchecks and the login page itself must stay reachable
    unauthenticated).
  - `base.html`'s nav is now conditional on `request.session.get('authenticated')`
    — logged-out visitors see no Controls/Dashboard/Log out links.
  - Added `.env.example` (`AUTH_USERNAME`, `AUTH_PASSWORD`,
    `SESSION_SECRET_KEY`) and wired the same three vars into
    `docker-compose.yml`'s `environment:` block via `${VAR:-default}`
    substitution, which docker compose auto-fills from a root `.env` file.
  - Logs a startup warning if `AUTH_PASSWORD` is still the default
    `changeme`, so it's obvious in the logs before exposing this beyond
    localhost.
  - Verified end-to-end: unauthenticated request to `/controls` redirects
    to `/login?next=/controls`; `/health` stays public; wrong password
    returns 401 with an inline error; correct login redirects back to the
    originally-requested `next` path; `/dashboard` and `/controls` both
    require the session; `/logout` clears it and re-protects immediately.
    Also verified visually with Playwright (login page renders correctly
    unauthenticated with no nav, and lands back on `/controls` with the
    full nav after a successful login) and validated `docker compose
    config` resolves the new env vars correctly, including the empty-string
    `SESSION_SECRET_KEY` edge case.
  - **Not yet done**: second framework support and connector checklists —
    Mike deferred the framework choice; connector checklists weren't
    selected in this pass. Both remain open Phase 5 items.
