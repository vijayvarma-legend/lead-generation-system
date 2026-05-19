# Lead Generation API

AI-powered backend for discovering local businesses, scoring their online presence, and generating personalized outreach messages.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2 (async) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| HTTP client | httpx (async) |
| Browser automation | Playwright (Chromium) |
| AI | OpenAI GPT-4o-mini |
| Lead scraping | Apify Google Maps actor |
| Logging | structlog (JSON) |
| Container | Docker + Docker Compose |

---

## Quick Start

### 1. Clone and configure

```bash
git clone <repo>
cd backend
cp .env.example .env
# Edit .env — set OPENAI_API_KEY, APIFY_API_TOKEN, DATABASE_URL
```

### 2. Run with Docker Compose

```bash
# Start DB + API
docker compose up -d

# Run migrations (one-time)
docker compose --profile migrate run migrate

# Check health
curl http://localhost:8000/api/v1/health
```

### 3. Local development (without Docker)

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

# Start Postgres locally, then:
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app factory
│   ├── core/
│   │   ├── config.py            # Pydantic settings (env-driven)
│   │   ├── database.py          # Async engine + session
│   │   ├── logging.py           # structlog JSON setup
│   │   └── security.py          # API key auth dependency
│   ├── models/
│   │   └── lead.py              # SQLAlchemy Lead ORM model
│   ├── schemas/
│   │   ├── lead.py              # Pydantic I/O schemas
│   │   ├── analysis.py          # Analysis/scoring/outreach schemas
│   │   └── common.py            # Pagination + envelope types
│   ├── repositories/
│   │   └── lead_repository.py   # Data-access layer (async)
│   ├── services/
│   │   ├── lead_collection_service.py   # Apify integration
│   │   ├── website_analysis_service.py  # Playwright scraper
│   │   ├── ai_service.py                # OpenAI outreach + scoring
│   │   └── scoring_service.py           # Heuristic fallback scorer
│   ├── routes/
│   │   ├── health.py
│   │   ├── leads.py
│   │   ├── analysis.py
│   │   ├── scoring.py
│   │   └── personalization.py
│   ├── prompts/
│   │   └── outreach_prompts.py  # Reusable prompt templates
│   ├── middleware/
│   │   ├── logging_middleware.py
│   │   └── error_handler.py
│   └── utils/
│       ├── helpers.py
│       └── validators.py
├── alembic/
│   ├── env.py
│   └── versions/001_initial_leads_table.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── alembic.ini
└── .env.example
```

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service + DB health check |

### Leads

| Method | Path | Description |
|---|---|---|
| POST | `/leads/collect` | Scrape leads from Google Maps via Apify |
| POST | `/leads` | Create a single lead manually |
| GET | `/leads` | List leads with filtering, sorting, pagination |
| GET | `/leads/{id}` | Get lead detail |
| PUT | `/leads/{id}` | Update lead fields |
| PATCH | `/leads/{id}/status` | Update workflow status |
| DELETE | `/leads/{id}` | Delete lead |

#### List leads — query parameters

| Param | Type | Description |
|---|---|---|
| `search` | string | Full-text search across name/address/category |
| `category` | string | Filter by business category |
| `status` | enum | `new`, `analyzed`, `scored`, `personalized`, etc. |
| `has_website` | bool | Filter by website presence |
| `min_score` / `max_score` | int 0-100 | AI score range |
| `min_rating` | float 0-5 | Minimum Google rating |
| `sort_by` | string | `ai_score`, `rating`, `created_at`, … |
| `sort_order` | `asc`/`desc` | |
| `page` / `page_size` | int | Pagination |

### Analysis

| Method | Path | Description |
|---|---|---|
| POST | `/analysis/{lead_id}` | Analyse website synchronously |
| POST | `/analysis/{lead_id}/async` | Queue analysis as background task |

### Scoring

| Method | Path | Description |
|---|---|---|
| POST | `/score/{lead_id}` | Generate AI lead score (0-100) |

Query param: `use_ai=true` (OpenAI) or `use_ai=false` (heuristic fallback).

### Personalization

| Method | Path | Description |
|---|---|---|
| POST | `/personalize/{lead_id}` | Generate email + WhatsApp + DM messages |

---

## Lead Score Breakdown

| Dimension | Max Points | Logic |
|---|---|---|
| Website existence | 25 | No website → 25 |
| Website quality | 25 | Poor quality → high score |
| Reviews & rating | 20 | Low/no reviews → high score |
| Social presence | 15 | No social links → high score |
| Mobile optimization | 15 | Not mobile-friendly → 15 |

Higher score = greater digital marketing opportunity.

---

## Lead Workflow States

```
new → analyzing → analyzed → scored → personalized → contacted → converted
                                                               ↓
                                                           rejected
```

---

## Environment Variables

See [`.env.example`](.env.example) for the full list. Required:

- `DATABASE_URL` — asyncpg connection string
- `OPENAI_API_KEY` — OpenAI API key
- `APIFY_API_TOKEN` — Apify platform token
- `SECRET_KEY` — app secret (use `openssl rand -hex 32`)
- `API_KEY` — header-based auth key (leave empty to disable)

---

## Database Migrations

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one step
alembic downgrade -1
```

---

## Authentication

Set the `API_KEY` env var to enable header-based authentication.

Protected endpoints require: `X-API-Key: <your-key>`

Leave `API_KEY` empty to disable auth (development mode).

---

## Extending the System

- **New lead sources**: add a service in `services/`, normalise to `LeadCreate`
- **New analysis signals**: extend `WebsiteAnalysisService._compute_quality_score()`
- **New outreach channels**: add a field to `OutreachMessages` and update the prompt in `prompts/outreach_prompts.py`
- **Background queues**: swap `BackgroundTasks` for Celery + Redis for heavy workloads
