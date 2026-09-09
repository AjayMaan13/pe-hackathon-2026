# FastAPI + Redis Migration Plan

Tracks the migration of the URL shortener from Flask to FastAPI, plus a Redis
caching layer in front of the redirect lookup. Scoped for the MLH Production
Engineering Hackathon 2026 (Reliability Engineering track).

Each phase below lands as its own commit (sometimes a couple of small
commits) so the history stays reviewable and bisectable. Flask stays live and
serving traffic until Phase 7 confirms full parity — nothing gets deleted
early.

DB access strategy: keep Peewee's synchronous calls as-is and let FastAPI run
route handlers in its threadpool (the default for `def`, not `async def`,
endpoints). This keeps the migration scoped to a weekend instead of a rewrite
onto `databases`/`asyncpg`. Documented here so it's not lost — this is the
answer to "why not async all the way."

## Phases

- [x] **Phase 1 — FastAPI skeleton, alongside Flask**
  App factory equivalent (`app/fastapi_app.py`), Pydantic schemas for
  `ShortenRequest`/`ShortenResponse`, a ported `/health` endpoint, structured
  JSON error handlers (400 on validation errors, 500 with no stack trace —
  matching `docs/ERROR_HANDLING.md`), a `run_fastapi.py` entry point, and a
  first FastAPI test using `TestClient`. Flask is untouched and still the
  app `docker-compose.yml` / CI run.

- [ ] **Phase 2 — Port `POST /shorten`**
  Move short-code creation to FastAPI using `ShortenRequest`/`ShortenResponse`
  for validation instead of the manual checks in `app/routes/urls.py`. Port
  the matching `TestShortenEndpoint` cases against the FastAPI `TestClient`.
  Same status codes and error JSON shape as today.

- [ ] **Phase 3 — Port `GET /<code>` (redirect)**
  Port the redirect lookup and its tests. No Redis yet — this phase is Postgres
  only, to keep the FastAPI parity change and the caching change reviewable
  separately.

- [ ] **Phase 4 — Port `GET /urls`**
  Port the list endpoint and its tests. At this point all 4 endpoints exist on
  FastAPI with passing tests and the coverage gate intact.

- [ ] **Phase 5 — Redis caching layer**
  `app/cache.py`: short_code → original_url cache with a TTL, sitting in front
  of the `GET /<code>` Postgres lookup from Phase 3. Cache is written/updated
  on `POST /shorten` and on cache miss. Redis failures fall back to Postgres
  rather than erroring the request (cache is an optimization, not a dependency
  the redirect path can't survive without). New tests cover hit, miss, and
  Redis-down fallback.

- [ ] **Phase 6 — Infra: docker-compose, env, Dockerfile**
  Add a `redis` service to `docker-compose.yml` (`restart: always`, matching
  the existing policy), add `REDIS_HOST`/`REDIS_PORT`/`REDIS_TTL_SECONDS` to
  `.env.example`, switch the app container's run command to uvicorn.

- [ ] **Phase 7 — Measure, then update docs**
  Capture a real before/after number for Redis (latency or DB query count on
  repeat reads — measured, not estimated) to use as the actual metric.
  Update `README.md` (stack line, setup steps, new env vars), and
  `docs/ERROR_HANDLING.md` / `docs/FAILURE_MODES.md` if FastAPI's exception
  handling changed any behavior from what's documented today.

- [ ] **Phase 8 — Remove Flask**
  Once Phases 2–7 are done and the full suite is green on FastAPI alone,
  delete `app/__init__.py`'s Flask factory, `app/routes/`, `run.py`, and the
  Flask/Peewee-via-Flask-hooks glue in `app/database.py` that only Flask
  used. Update `pyproject.toml` to drop the `flask` dependency and the
  Dockerfile `CMD`.

## Non-goals (unchanged from the brief)

- No new endpoints beyond the existing 4.
- No chaos-engineering tooling.
- No auth/user accounts.
- Reliability docs must stay true to what's actually implemented — update
  them alongside any behavior change, not after.

## Acceptance criteria

- All 4 endpoints behave identically from the outside (same request/response
  shapes, same status codes for the same inputs).
- Test suite passes with coverage at or above the current 96% baseline.
- Redis cache has a measured before/after number, not an estimate.
- `README.md` reflects the real stack and setup steps once Phase 7 lands.
