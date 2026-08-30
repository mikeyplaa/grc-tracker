# Personal GRC / Compliance Tracker — Project Brief

## What this is
A self-hosted, single-user compliance and evidence-tracking tool, modelled loosely on
Drata's core loop (controls → evidence → scoring → dashboard), scaled down for personal
use as a CISO-portfolio artifact and a live tracker of Mike's own security documentation
and control maturity.

This is NOT a commercial SaaS build. No multi-tenancy, no auth complexity, no billing.
Optimise for: fast to build, easy to run locally/on the home lab, genuinely useful day to
day, and demo-able as a portfolio piece.

## Owner context (for tone/scope decisions)
- Head of Cyber Security at a telematics/connected-vehicle data company; owns the
  ISO 27001:2022 programme there.
- Runs a segmented Proxmox home lab — this app should be dockerised and deployable there.
- On a CISO-track path; wants this partly as a working tool, partly as an interview/
  portfolio artifact demonstrating hands-on GRC engineering.
- Prior Claude Code projects used a CLAUDE.md + NEXT_STEPS.md iterative workflow —
  keep that pattern here.

## Core loop (MVP)
1. **Framework** — seed with ISO 27001:2022 Annex A controls (93 controls, 4 themes:
   Organizational, People, Physical, Technological).
2. **Control record** — each control has: id, title, description, theme, status
   (Not Started / In Progress / Implemented / Evidenced), owner note, last-reviewed date.
3. **Evidence** — files/links attached to a control (policy doc, screenshot, config
   export, ticket link). Each evidence item has an upload date and optional expiry/
   review-due date.
4. **Scoring** — weighted roll-up:
   - Not Started = 0, In Progress = 0.33, Implemented = 0.66, Evidenced = 1.0
   - Overall % = mean across all controls; also break down by theme.
   - "Stale" flag if evidence review-due date has passed — stale evidence should pull
     the control's effective score down a tier until refreshed.
5. **Dashboard** — overall score, score-by-theme bar chart, score-over-time trend
   (snapshot on each scoring run), list of gaps (Not Started / In Progress) and stale
   items sorted by urgency.
6. **Export** — one-click summary (PDF or Markdown) suitable for a portfolio artifact
   or a quick self-audit report.

## Explicitly out of scope for MVP
- Multiple frameworks at once (design the data model to allow it later, but seed only
  ISO 27001:2022 first)
- Multi-user / RBAC
- Automated evidence collection from cloud APIs (Drata's big differentiator — nice
  future phase, not MVP)
- Questionnaire/vendor-risk automation
- SSO/auth beyond a single local login or no auth at all (home-lab network only)

## Suggested stack (matches prior project pattern)
- Backend: Python + FastAPI
- DB: SQLite to start (simple, file-based, fits single-user); design models so a
  swap to Postgres is trivial later
- Frontend: Keep simple — server-rendered Jinja2 templates + a bit of HTMX, or a
  lightweight React/Vite SPA if Mike prefers a more polished portfolio look. Default
  to the simpler server-rendered option unless told otherwise.
- Containerised with Docker / docker-compose, deployable to the Proxmox lab
- Charts: Chart.js or similar, kept lightweight

## Data model (starting point)
```
Control
  id (e.g. "A.5.1")
  theme (Organizational | People | Physical | Technological)
  title
  description
  status (enum)
  owner_note (text)
  last_reviewed (date, nullable)

Evidence
  id
  control_id (FK)
  title
  file_path_or_url
  uploaded_at
  review_due (date, nullable)

ScoreSnapshot
  id
  taken_at (timestamp)
  overall_score
  theme_scores (json: {theme: score})
```

## Working agreement for Claude Code sessions
- Keep NEXT_STEPS.md up to date at the end of every session — what's done, what's next.
- Prefer small, working vertical slices over big-bang builds: get one control type
  end-to-end (create → view → attach evidence → score) before building out the rest.
- Seed data for the 93 ISO 27001:2022 Annex A controls should be sourced accurately —
  flag to Mike if unsure of exact control wording rather than guessing.
- Ask before introducing new major dependencies or infrastructure (e.g. swapping to
  Postgres, adding an auth layer).
