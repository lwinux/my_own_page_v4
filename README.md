# MyOwnPage v4

> **Create and publish tailored profile pages for every job opportunity.**
> Each profile = a unique public URL. Publish a new version → new token → new URL.

---

## Architecture

```
                        ┌─────────────┐
    Browser ──────────► │ nginx proxy │ :80
                        └──────┬──────┘
                               │
          ┌────────────────────┼──────────────────────┐
          │                    │                       │
     /app/*              /api/*              /<slug>-<token>
          │                    │                       │
    ┌─────▼──────┐    ┌────────▼───────┐    ┌─────────▼──────┐
    │ frontend1  │    │    backend     │    │   frontend2    │
    │ Flask :5001│    │ FastAPI :8000  │    │  Flask :5002   │
    │ Dashboard  │    │ JSON API only  │    │ Public landing │
    └────────────┘    └───────┬────────┘    └────────────────┘
                              │
                   ┌──────────┴──────────┐
                   │                     │
            ┌──────▼──────┐    ┌─────────▼──────┐
            │  PostgreSQL │    │     Redis       │
            │  (profiles, │    │  (draft JSON,   │
            │  versions)  │    │   TTL 7 days)   │
            └─────────────┘    └────────────────┘
```

### Services

| Service       | Port | Role |
|---------------|------|------|
| reverse-proxy | 80   | Nginx routes: `/app` → frontend1, `/api` → backend, `/*` → frontend2 |
| backend       | 8000 | FastAPI JSON REST API. No HTML templates. |
| frontend1     | 5001 | Flask dashboard. Reads/writes backend via HTTP. No direct DB access. |
| frontend2     | 5002 | Flask public landing. Reads `/api/public/<token>` and renders profile. |
| postgres      | 5432 | Persistent profile data + version history. |
| redis         | 6379 | Draft storage with 7-day TTL. |

---

## Quick Start

```bash
# 1. Clone & configure
cd my_own_page_v4
cp .env.example .env
# Edit .env — minimum required changes:
#   POSTGRES_PASSWORD=<your-password>
#   JWT_SECRET_KEY=<min-32-chars>         # python -c "import secrets; print(secrets.token_hex(32))"
#   FRONTEND1_SECRET_KEY=<random-string>
#   SESSION_COOKIE_SECURE=false           # ⚠️  keep false for HTTP; set true only with HTTPS

# 2. Start all 6 services
docker compose up --build

# 3. Open in browser
open http://localhost/app
```

### First-time setup flow

1. Register at `http://localhost/app/register`
2. Create a profile (give it a name like "Senior Engineer @ Stripe")
3. Open the editor — fill in your CV blocks
4. Click **Save Draft**  → stored in Redis
5. Click **Publish**     → new version in Postgres, unique public URL returned
6. Share the URL: `http://localhost/<profile_slug>-<64-hex-token>`

---

## API Reference

Base: `http://localhost/api`

### Auth

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create user `{email, username, password}` |
| POST | `/auth/login` | Returns `{access_token, refresh_token}` |
| POST | `/auth/refresh` | Exchange refresh token for new pair |
| POST | `/auth/logout` | Client-side token discard (stateless) |

### Profiles (auth required)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/profiles` | Create profile `{profile_name, company_note}` |
| GET | `/profiles` | List all profiles with latest version link |
| GET | `/profiles/<id>` | Profile detail + all versions |
| PATCH | `/profiles/<id>` | Update `profile_name` and/or `company_note` |

### Draft (Redis, auth required)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/profiles/<id>/draft` | Load current draft from Redis |
| PUT | `/profiles/<id>/draft` | Validate + save draft (ProfileData v1 JSON) |
| DELETE | `/profiles/<id>/draft` | Discard draft |

### Publish (Postgres, auth required)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/profiles/<id>/publish` | Draft → new version in Postgres. Returns `{public_url, token, version_number}` |
| GET | `/profiles/<id>/versions` | List all published versions |

### Public (no auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/public/<token>` | Returns profile JSON for frontend2 |

### Interactive docs
`http://localhost/api/docs`

---

## ProfileData v1 Schema

```json
{
  "schema_version": 1,
  "personal": {
    "full_name": "string (required)",
    "title": "string (required)",
    "email": "email (required)",
    "phone": "string | null",
    "location": "string | null",
    "linkedin": "url | null",
    "github": "url | null",
    "website": "url | null",
    "summary": "string (required)"
  },
  "experience": [
    {
      "company": "string (required)",
      "position": "string (required)",
      "start_date": "YYYY-MM (required)",
      "end_date": "YYYY-MM | null",
      "location": "string | null",
      "description": "string | null",
      "highlights": ["string"]
    }
  ],
  "education": [{ "institution", "degree", "field", "start_date", "end_date", "gpa" }],
  "skills": [{ "category": "string", "items": ["string"] }],
  "projects": [{ "name", "description", "url", "tech_stack", "highlights" }],
  "languages": [{ "language": "string", "proficiency": "Native|Fluent|Advanced|Intermediate|Basic" }],
  "certifications": [{ "name", "issuer", "date", "url" }]
}
```

Validated by Pydantic v2 on every `PUT /draft` and `POST /publish`.

---

## Running Tests

```bash
# Inside the backend container
docker compose exec backend pytest tests/ -v

# Or locally (requires aiosqlite)
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Test coverage:
- `test_auth.py`    — register, login, refresh, duplicate detection, 401 guard
- `test_draft.py`   — save/load/delete draft, validation errors
- `test_publish.py` — publish, version increment, unique tokens, no-draft 404
- `test_public.py`  — token lookup, 404 for unknown token, slug/URL consistency

---

## Database Migrations

```bash
# Apply migrations (auto-run at container startup via entrypoint.sh)
docker compose exec backend alembic upgrade head

# Generate a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "add column x"

# Rollback one step
docker compose exec backend alembic downgrade -1
```

---

## Environment Variables

See `.env.example` for all variables. Key ones:

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `JWT_SECRET_KEY` | ✅ | Min 32 chars — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FRONTEND1_SECRET_KEY` | ✅ | Flask session signing key — same generation command |
| `SESSION_COOKIE_SECURE` | ✅ | **`false` for HTTP** (local/dev). Set `true` only when serving over HTTPS. Wrong value here causes login session to silently drop and redirect-loop back to `/app/login`. |
| `FEATURE_RATE_LIMITING` | — | `true`/`false` (default: `true`) |
| `FEATURE_PDF_EXPORT` | — | Future: PDF export toggle |
| `FEATURE_THEMES` | — | Future: profile theme selection |

---

## Extending the System

### Add a new profile block (e.g. "Awards")

1. **Backend schema** — add `AwardItem` model + `awards: list[AwardItem] = []` to `ProfileData` in `backend/app/schemas/profile_data.py`
2. **Alembic** — no migration needed (stored as JSONB)
3. **frontend1 editor** — add `buildAwardCard()` to `editor.js`, register in `BUILDERS`, hydrate in `hydrate()`
4. **frontend2 template** — add an `{% if p.awards %}` section in `profile/view.html`

### Add PDF export

1. Set `FEATURE_PDF_EXPORT=true` in `.env`
2. Add a `GET /api/profiles/<id>/versions/<version_id>/pdf` endpoint in the backend using `weasyprint`
3. Add "Download PDF" button in frontend1 editor and frontend2 public page

### Add profile themes

1. Set `FEATURE_THEMES=true` in `.env`
2. Add `theme: str = "default"` to `ProfileData`
3. In frontend2, select the template based on `profile.json_data.theme`

---

## Acceptance Criteria

- [ ] `docker compose up` starts **6 services**: proxy, frontend1, backend, frontend2, postgres, redis
- [ ] Dashboard loads at `http://localhost/app`
- [ ] API responds at `http://localhost/api/health`
- [ ] Docs available at `http://localhost/api/docs`
- [ ] Register → Login → Create profile → Edit → Save Draft (Redis) → Publish (Postgres) → Public URL works
- [ ] Each Publish creates a new version with a unique 64-char token
- [ ] Draft survives page reload (loaded from Redis on editor open)
- [ ] Public page renders at `http://localhost/<slug>-<token>` via frontend2 → backend call
- [ ] Backend returns no HTML — only JSON
