# grc-tracker

Self-hosted, single-user GRC / compliance tracker: controls → evidence → scoring →
dashboard, plus a **public trust centre** for the controls you choose to publish.

Frameworks seeded: ISO 27001:2022 Annex A (93), SOC 2 (43), ISO/IEC 42001:2023
Annex A (38).

## Run it locally (Docker)

```bash
cp .env.example .env    # set AUTH_PASSWORD, SESSION_SECRET_KEY, TRUST_ORG_NAME
docker compose up --build -d
```

Then open `http://localhost:${APP_PORT:-8000}`.

| Surface | URL | Access |
| --- | --- | --- |
| Admin — controls, evidence, dashboard, export | `/controls`, `/dashboard` | single login (`AUTH_USERNAME` / `AUTH_PASSWORD`) |
| Public trust centre | `/trust` | **no login** |

Bare dev run without Docker (SQLite, migrates and seeds itself on startup):

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Trust centre

`/trust` is the one unauthenticated surface. It shows, per framework:

- implementation score computed over **published controls only**,
- score by theme,
- each published control's ID, title, description, status and last-reviewed date,
- evidence **count and last-refreshed date**, plus a "review overdue" flag.

Nothing appears there until you publish it. Publishing is per control, from the
control's admin page ("Publish to trust centre"); a framework tab appears once at
least one of its controls is published. Owner notes, evidence titles, evidence
links and uploaded files are never published — see `app/trust.py`, which maps
controls to a `PublicControl` carrying only publishable fields.

Branding comes from `TRUST_ORG_NAME` and `TRUST_CONTACT_EMAIL`.

> The trust centre has no auth in front of it by design. Only expose the app's
> port to networks you're happy for that page to be readable from.
