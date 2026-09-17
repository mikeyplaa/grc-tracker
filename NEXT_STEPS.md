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
- [x] Second framework support (SOC 2) using the same control/evidence model
- [x] Simple auth (single local login) if exposing beyond the lab network
- [ ] Manual "connector" style checklist prompts (poor-man's automated evidence)

## Phase 6 — Multi-user (RBAC on one shared programme)
Decision (2026-09-02): Mike needs multi-user. Scope confirmed as **RBAC on a single
shared programme** (all users collaborate on the same controls/evidence; differences
are role-based), ~<20 internal users, home-lab/VPN only, not internet-exposed. This
supersedes CLAUDE.md's "multi-user out of scope" line for the shared-programme case
only — still NOT multi-tenancy / isolated workspaces.

- [x] **Slice 1 — Postgres + Alembic** (current schema, no behaviour change)
  - Add `alembic` + `psycopg[binary]` to requirements
  - `db` service in docker-compose (postgres:16 + healthcheck + named volume);
    app `depends_on` db healthy; `DATABASE_URL` → postgres in compose
  - Alembic scaffold; initial migration matching the current models
  - Startup runs `alembic upgrade head` instead of `Base.metadata.create_all`
  - SQLite stays the default for bare `uvicorn` dev runs
- [ ] **Slice 2 — User model + DB-backed auth**
  - `User`: email, `password_hash` (argon2), `role` enum, `is_active`, `created_at`
  - Replace env-var single login in `app/auth.py`; keep `SessionMiddleware`
  - First-run bootstrap: create an admin from `AUTH_USERNAME`/`AUTH_PASSWORD`
    when the users table is empty (keeps deploy one step)
- [ ] **Slice 3 — Roles + enforcement**
  - `require_role(...)` dependency: viewer = read-only, contributor = edit
    controls/evidence/snapshots, admin = also manage users
- [ ] **Slice 4 — Attribution + audit log**
  - `updated_by` on status changes, `uploaded_by` on evidence, optional
    `owner_id` FK on `Control`; lightweight activity-log table (who/what/when)
- [ ] **Slice 5 — User-management UI** (admin only): create / deactivate /
  set role / reset password
- [ ] **Slice 6 — CSRF tokens** on the mutating forms

## Phase 7 — Public trust centre
Decision (2026-09-17): Mike wants the tracker to double as a trust centre —
one user, local Docker, for now. Confirmed scope: a public page **alongside**
the existing authenticated admin (not replacing it, not a second service),
per-control status detail, **no gate** on the public page, and an **explicit
publish flag per item** so nothing is public by default.

- [x] **Slice 1 — publishable controls + public /trust surface**
  - `Control.is_public` / `Control.published_at`; per-control publish toggle in
    the admin UI
  - Unauthenticated `/trust` (framework tabs, score over published controls
    only, theme breakdown, published control list) and `/trust/controls/{id}`
  - Evidence published as count + last-refreshed + overdue flag only
  - `TRUST_ORG_NAME` / `TRUST_CONTACT_EMAIL` branding
- [ ] **Slice 2 — published documents** (policy PDFs, cert letters): a
  `Document` model with the same explicit publish flag, some downloadable,
  some "available on request". Deferred from slice 1 — Mike picked control
  detail only for the first pass.
- [ ] **Slice 3 — subprocessors / security FAQ / vuln-disclosure contact**
  sections, curated in admin
- [ ] **Slice 4 — gated documents** (access request captured in admin) if the
  trust centre ever faces a real customer rather than the lab
- [ ] **Slice 5 — public score trend** from `ScoreSnapshot`, restricted to
  published controls (needs published-only snapshots; today's snapshots cover
  every control, so they cannot be shown publicly as-is)

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
  deferred the second-framework item to specify separately later (he then
  came back and picked SOC 2 — see below, merged together in this commit).
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
- **Phase 5 — second framework (SOC 2) complete.** This turned out to be a
  bigger change than "just add more seed data": the schema as originally
  built (Phase 1) only really supported one framework — `Control.theme` was
  a strict ISO-specific enum, and every score/gap/export computation summed
  across *all* controls regardless of framework. Blending ISO 27001 and
  SOC 2 controls into one "overall score" would have been actively
  misleading, so this was a real (if modest) schema + logic generalization,
  not a pure addition. No Alembic migration — no production data exists yet
  (Proxmox deploy is still pending), so schema changes just apply on a fresh
  `Base.metadata.create_all()`. **Flag**: if you've already run this
  locally and have a `data/grc_tracker.db` with the old schema, delete it
  before running the new code — this is the second time schema evolved
  without a migration tool; worth adopting Alembic once real evidence data
  exists that you'd lose by dropping the db.
  - `Control` gains a `framework` column (`ControlFramework` enum:
    `ISO_27001_2022` / `SOC_2`); `theme` changed from a strict ISO-only enum
    to a plain string so each framework can use its own category vocabulary
    (ISO's 4 themes vs. SOC 2's Trust Services Criteria categories) without
    enum bloat. `ScoreSnapshot` also gains a `framework` column so trend
    history is framework-scoped, not blended.
  - `app/frameworks.py`: single source of truth for framework metadata —
    slugs (`iso27001`/`soc2`) used in URLs, per-framework theme ordering,
    per-framework seed file paths, and a generalized `natural_sort_key()`
    that replaces the old ISO-specific `id.split(".")` sort (which would've
    broken on SOC 2 IDs like `CC1.1` — regex-based digit/text-run splitting
    handles both `A.5.9`-before-`A.5.10` and `CC1.1`-before-`CC1.2` the
    same way).
  - `data/soc2_2017_tsc.json`: 43 controls — the 33-criterion Security
    ("Common Criteria" CC1–CC9, mandatory in every SOC 2 report) plus
    Availability (3), Confidentiality (2), and Processing Integrity (5).
    **Flag for Mike** (same policy as the ISO seed): IDs/categories/short
    titles are high-confidence (the Common Criteria structure is extremely
    widely published). Descriptions are my own paraphrase, not verbatim
    AICPA TSC text — same copyright + accuracy reasoning as ISO. **Privacy
    category deliberately omitted**: my confidence in its exact sub-criteria
    numbering (P1.1 through P8.x) is meaningfully lower than the other four
    categories, and it's also the least commonly scoped-in category in real
    SOC 2 engagements — flagging rather than guessing. Add it later against
    an official AICPA TSC document if you need full Privacy coverage.
  - `app/seed.py` now loops `FRAMEWORK_SEED_FILES` and seeds both frameworks;
    still idempotent, still safe to re-run, still called on app startup.
  - Every route that touches scoring is now framework-scoped via a
    `?framework=iso27001|soc2` query param (default `iso27001` for
    backward-compat): `GET /controls`, `GET /dashboard`,
    `POST /dashboard/snapshot`, `GET /export/markdown`, `GET /export/pdf`.
    `GET /controls/{id}` and its status/evidence POSTs stay unprefixed —
    control IDs are still globally unique (ISO's `A.N.M` vs. SOC 2's
    `CC/A/C/PI` prefixes don't collide), so no ambiguity from dropping the
    framework segment there.
  - Added tab-style framework switchers (`.tabs` in `base.html`) to the
    controls list and dashboard pages. Header tagline/footer changed from
    the ISO-only text to a framework-neutral one.
  - Verified end-to-end: seeded both frameworks (93 + 43 = 136 total,
    correct per-theme counts on both sides), set statuses/evidence
    independently on each framework and confirmed dashboards don't
    cross-contaminate (an ISO status change doesn't move the SOC 2 score
    and vice versa), confirmed natural sort order on SOC 2's `CC6.1`.`CC6.8`
    run, verified snapshots are stored and read back per-framework, and
    checked Markdown/PDF export output and headers for both frameworks.
    Also verified visually with Playwright screenshots of the SOC 2 tab on
    both `/controls` and `/dashboard`.
- **Phase 5 status after merging auth (#9) and SOC 2 (#10) together**: both
  simple auth and the second framework are now complete. The only open
  Phase 5 item is manual "connector" style checklist prompts. Outside
  Phase 5, the Proxmox deployment step (Phase 4) is still pending Mike's
  lab access.
- **Phase 6 slice 1 — Postgres + Alembic complete (2026-09-02).** No app
  behaviour change; this is pure infrastructure so slices 2–6 land on a real
  migration tool.
  - `requirements.txt`: added `alembic==1.14.0`, `psycopg[binary]==3.2.3`.
  - Alembic scaffold: `alembic.ini` (URL comes from app settings, not the
    ini), `alembic/env.py`, `alembic/script.py.mako`,
    `alembic/versions/0001_initial_schema.py`. `env.py` pulls
    `sqlalchemy.url` from `get_settings().database_url` and imports
    `app.models` so autogenerate sees the tables. Batch mode is enabled only
    on SQLite (keeps future `ALTER`s working there; no-op on PG).
  - **Enum gotcha handled**: SQLAlchemy persists the enum *member names*
    (`ISO_27001_2022`, `NOT_STARTED`, …), not the `.value` strings — verified
    against the existing SQLite db. The initial migration creates the PG
    `controlframework` / `controlstatus` types with those exact labels. The
    two enum types are created once via explicit `.create(checkfirst=True)`
    with `create_type=False` on the columns, so sharing `controlframework`
    across `controls` + `score_snapshots` doesn't double-CREATE TYPE on PG.
  - `app/main.py`: startup now runs `alembic upgrade head` programmatically
    (`run_migrations()`) before `seed_controls()`, replacing
    `Base.metadata.create_all`. `app/seed.py` lost its `create_all` call too.
  - **docker-compose.yml**: new `db` service (`postgres:16`, `pg_isready`
    healthcheck, named volume `db_data`); `app` gains
    `depends_on: db: condition: service_healthy` and
    `DATABASE_URL=postgresql+psycopg://…@db:5432/…` built from
    `POSTGRES_USER/PASSWORD/DB` (defaults `grc`/`grc`/`grc`). Added those
    three vars to `.env` / `.env.example`.
  - `config.py` default `database_url` stays SQLite, so a bare
    `uvicorn app.main:app` dev run still works with zero setup (and now
    migrates itself on startup).
  - `docker/Dockerfile`: also copies `alembic/`, `alembic.ini`, and
    `data/*.json` (seed files — image is now self-contained; the SQLite
    db / evidence uploads still come from the mounted volume). Added
    `.dockerignore`.
  - **Verified in Docker** (daemon was available this session): `docker
    compose up --build` → migration runs (`0001_initial`), 136 controls
    seed, `/health` 200. Full auth flow via curl: login, `/controls`,
    status updates on both frameworks (writes the PG enum correctly —
    checked `A.5.1`=IMPLEMENTED, `CC1.1`=IN_PROGRESS in psql),
    `/dashboard/snapshot`, `/dashboard`, `/export/markdown`, `/export/pdf`
    all 200/303. `alembic check` reports no drift vs. the models. Also ran
    the migration up+down against SQLite in the image — both dialects clean.
  - **Stale artefact**: `data/grc_tracker.db` (old SQLite, pre-Postgres) is
    now unused — safe to delete. It's gitignored so it won't be committed.
  - Local run is now: `docker compose up --build -d` then open
    `http://localhost:${APP_PORT}` (`.env` currently sets `APP_PORT=8001`).
- **Third framework — ISO/IEC 42001:2023 (AI management system) added
  (2026-09-02).** Same multi-framework mechanism as SOC 2; branched off the
  Postgres slice (`claude/phase6-iso42001`).
  - `ControlFramework` enum gains `ISO_42001_2023`; slug `iso42001`; 9 Annex A
    control objectives (A.2–A.10) as the theme vocabulary in `frameworks.py`.
  - `data/iso42001_2023_annex_a.json`: 38 Annex A reference controls
    (3/2/5/4/9/5/4/3/3 across the nine objectives). **Flag for Mike** (same
    policy as the ISO 27001 / SOC 2 seeds): IDs, objective groupings and short
    titles are the widely-published Annex A structure (high confidence);
    `description` is my own paraphrase, not verbatim ISO text — swap in wording
    from a licensed copy of the standard for the portfolio artifact.
  - **ID-collision decision (Option A, chosen by Mike):** ISO 42001 Annex A
    reuses ISO 27001's `A.<n>.<m>` notation and the numbers overlap (`A.5.2`,
    `A.7.2`–`A.7.6`, `A.8.2`–`A.8.5` exist in both). `Control.id` is still a
    global PK, so ISO 42001 IDs are stored **and displayed** with an `AI.`
    prefix (`AI.5.2` = ISO 42001 Annex A 5.2). No display-mapping layer — a
    consistent `AI.` prefix was preferred over a bug-prone
    show-`A.5.2`-but-store-`AI.5.2` split. The proper fix (composite
    `(framework, control_id)` key) is noted as a possible later slice if the
    prefix ever grates.
  - `alembic/versions/0002_add_iso42001_framework.py`: `ALTER TYPE
    controlframework ADD VALUE IF NOT EXISTS 'ISO_42001_2023'` inside an
    `autocommit_block()` (PG only; no-op on SQLite). Downgrade is a documented
    no-op (PG can't drop one enum label without recreating the type).
  - Verified in Docker: incremental upgrade `0001 -> 0002` and a
    from-scratch fresh DB both run clean; 93 + 43 + 38 = 174 controls seed;
    `alembic check` no drift; SQLite up/down/up chain clean; full app flow on
    `?framework=iso42001` (list of 38, status write on `AI.6.2.4`, snapshot,
    dashboard, markdown + PDF export) all green; ISO 27001 / SOC 2 dashboards
    unaffected; three framework tabs render.

- **Phase 7 slice 1 — public trust centre (2026-09-17).** Branch
  `claude/trust-centre-docker-local-rcf7lt`. Answers Mike gave up front, which
  shaped the whole slice: public page **plus** admin behind login (one app, one
  container); per-control status detail as the published content; **no gate**;
  explicit per-item publish flag; evidence as **count + freshness only**; score
  computed over **published controls only**; `last_reviewed` shown publicly;
  `owner_note` **hidden** (admin-only); branding from env vars.
  - `Control` gains `is_public` (bool, default false, NOT NULL) and
    `published_at`. `alembic/versions/0003_add_control_publishing.py` adds both
    in a `batch_alter_table` with `server_default=sa.false()` so the columns can
    be added to a table already holding 174 rows. Existing rows stay
    unpublished — turning this on exposes nothing by itself.
  - `app/trust.py` is the whole public read path. Controls are mapped to a
    frozen `PublicControl` dataclass that has **no field for `owner_note` and
    no field for evidence titles/locations**, so a future template edit cannot
    leak them. `public_control_or_none()` returns the same `None` for "unknown
    ID" and "not published", so `/trust` can't be used to probe which control
    IDs are being held back.
  - `app/routers/trust.py` is mounted in `main.py` **without** the
    `require_login` dependency the other three routers carry — the one
    deliberate public surface. Routes: `GET /trust` (optional
    `?framework=<slug>`) and `GET /trust/controls/{id}`.
  - **Framework visibility is derived, not separately toggled**: a framework tab
    appears exactly when ≥1 of its controls is published (`published_frameworks()`).
    `ControlFramework` is an enum, not a table, so a framework-level flag would
    have meant a new table and a second publishing switch to reason about —
    deriving it keeps one switch. `?framework=` pointing at a framework with
    nothing published falls back to the first one that has something, so the
    landing page is never an empty tab.
  - **Scoring**: reuses `compute_scores()` over the published subset, with the
    theme list narrowed to themes that actually have published controls — the
    public number is never a function of anything unpublished. The admin
    dashboard is untouched and still scores all controls (verified: 93 controls
    / 91 gaps on ISO after publishing 8 of them).
  - `published_at` doubles as "public record last changed": `_touch_public_record()`
    in `app/routers/controls.py` bumps it on a status change or evidence upload
    **if** the control is published, so the trust centre's "Last updated" stays
    honest. Unpublishing clears it.
  - Templates: new `trust_base.html` (public shell — no admin nav, no
    session-dependent links, `noindex`), `trust_index.html`, `trust_control.html`,
    `trust_empty.html`. The inline `<style>` block moved out of `base.html` into
    `app/static/css/app.css` so both shells share one stylesheet; trust-centre
    styles are appended there.
  - Admin UI: publish/unpublish button + "what publishing exposes" note on the
    control page, `Published` badge column on the controls list, published count
    in the list header, `Trust Centre` link in the nav.
  - `TRUST_ORG_NAME` (default `Your Organisation`) and `TRUST_CONTACT_EMAIL`
    (blank hides the contact line) added to `config.py`, `.env.example` and the
    compose app service.
  - **Verified** (SQLite + uvicorn; no Docker daemon in this session):
    migrations `0001→0003` from scratch, 174 controls seeded; `/trust`
    unauthenticated 200 with the empty state, then with published controls;
    `/trust/controls/{id}` 404 for both unpublished and unknown IDs; `/controls`,
    `/dashboard`, `/export/*` and `POST /controls/{id}/publish` all still 303 to
    `/login` when unauthenticated (and an unauthenticated publish POST left
    `is_public=0` in the DB); scores checked by hand (A.5.1 Evidenced = 1.0,
    A.5.2 Implemented with stale evidence = 0.33 via the stale tier-drop, A.6.1
    In Progress = 0.33 → Organizational 66%, People 33%, overall 55%); grepped
    the public HTML for the owner note, evidence titles, evidence URLs and any
    `/controls/...` admin link — none present; SOC 2 tab scores independently;
    unpublishing the last control of a framework removes its tab and
    unpublishing everything returns the empty state; `alembic check` reports no
    drift and `0003` down+up is clean on SQLite; the Postgres DDL was rendered
    offline (`alembic upgrade --sql`) and is `ALTER TABLE controls ADD COLUMN
    is_public BOOLEAN DEFAULT false NOT NULL` as intended.
    **Not verified against a live Postgres or in Docker this session** (no
    daemon available) — worth one `docker compose up --build` on the lab box.
  - Screenshots taken with Playwright (public index, public control detail,
    admin control page).
  - **Flag for Mike**: the public page's disclaimer says evidence is "available
    under NDA on request" — reword it in `trust_index.html` /
    `trust_control.html` if that is not the posture you want, and set
    `TRUST_ORG_NAME` / `TRUST_CONTACT_EMAIL` before showing it to anyone.
