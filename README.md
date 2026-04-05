# PE Hackathon — URL Shortener

A production-hardened URL shortening service built for the MLH Production Engineering Hackathon.

**Track:** Reliability Engineering  
**Stack:** Flask · Peewee ORM · PostgreSQL · pytest · GitHub Actions

![Tests](https://github.com/AjayMaan13/pe-hackathon-2026/actions/workflows/test.yml/badge.svg)

---

## Setup

### Prerequisites
- Python 3.12+
- PostgreSQL running locally (or Docker)
- [uv](https://docs.astral.sh/uv/) installed

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Quick Start

```bash
# 1. Clone
git clone https://github.com/AjayMaan13/pe-hackathon-2026.git
cd pe-hackathon-2026

# 2. Install dependencies
uv sync

# 3. Create database
createdb hackathon_db
# OR with Docker:
# docker run --name hackathon-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=hackathon_db -p 5432:5432 -d postgres

# 4. Configure
cp .env.example .env
# Edit .env if your DB credentials differ

# 5. Run
uv run run.py
```

Visit http://localhost:8080/health — should return `{"status": "ok"}`

### Run with Docker (auto-restart on crash)

```bash
docker compose up --build
```

Visit http://localhost:8081/health

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| POST | `/shorten` | Shorten a URL |
| GET | `/<code>` | Redirect to original URL |
| GET | `/urls` | List all shortened URLs |

### POST /shorten

**Request:**
```json
{ "url": "https://example.com/very/long/path" }
```

**Response (201):**
```json
{
  "short_code": "aB3xZ9",
  "short_url": "http://localhost:8080/aB3xZ9",
  "original_url": "https://example.com/very/long/path"
}
```

**Errors:**
- `400` — Missing or invalid URL
- `500` — Server error

---

## Running Tests

```bash
uv run pytest tests/ -v
```

With coverage:
```bash
uv run pytest tests/ --cov=app --cov-report=term-missing
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_NAME` | PostgreSQL database name | `hackathon_db` |
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_USER` | PostgreSQL user | `postgres` |
| `DATABASE_PASSWORD` | PostgreSQL password | `postgres` |

---

## Architecture

```
Client (browser / curl)
        │
        ▼
  Flask App (port 8080)
        │
        ▼
  Peewee ORM
        │
        ▼
  PostgreSQL Database
```

---

## Project Structure

```
pe-hackathon-2026/
├── app/
│   ├── __init__.py          # App factory
│   ├── database.py          # DB connection wiring
│   ├── models/
│   │   ├── __init__.py      # Model registration
│   │   └── url.py           # URL model + short code generator
│   └── routes/
│       ├── __init__.py      # Blueprint registration
│       └── urls.py          # URL shortener endpoints
├── tests/
│   ├── conftest.py          # pytest fixtures
│   └── test_urls.py         # 23 tests
├── docs/
│   ├── ERROR_HANDLING.md    # Error codes and response formats
│   └── FAILURE_MODES.md     # What happens when things break
├── .github/workflows/
│   └── test.yml             # CI — runs tests + coverage on every push
├── Dockerfile               # Container definition
├── docker-compose.yml       # App + DB with auto-restart
├── setup_db.py              # One-time table creation script
└── run.py                   # Entry point
```

---

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

---

## Reliability Features

- **Health endpoint** — `GET /health` always returns 200 if the service is up
- **Input validation** — rejects malformed URLs with a 400 JSON error, never crashes
- **23 automated tests** — unit + integration coverage across all endpoints
- **96% test coverage** — measured with pytest-cov, enforced in CI
- **GitHub Actions CI** — tests run on every push, fails if coverage drops below 50%
- **Docker restart policy** — `restart: always` auto-recovers from crashes in 2-5 seconds
- **Graceful errors** — all errors return JSON, no stack traces exposed to users
