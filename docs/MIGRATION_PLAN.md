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

- [x] **Phase 2 — Port `POST /shorten`**
  Moved short-code creation to FastAPI using `ShortenRequest`/`ShortenResponse`
  — a `field_validator` on `ShortenRequest.url` replaces the manual empty/protocol
  checks, and the app-level `RequestValidationError` handler surfaces that
  validator's message so the JSON error text is byte-identical to Flask's
  (verified against every case in `docs/ERROR_HANDLING.md`). Ported all 9
  `TestShortenEndpoint` cases plus a new test for the unhandled-exception path
  (500, JSON, no stack trace — matches `docs/FAILURE_MODES.md`).

  Also fixed a real bug from Phase 1: the ASGI-level DB connect/close
  middleware was a no-op for real queries, because Peewee's connection state
  is thread-local and FastAPI's threadpool doesn't guarantee a request's
  middleware and its sync route body share a thread. Replaced it with
  `db_session()`, a context manager entered inside each DB-touching route
  function so connect/close always happen on the same thread as the query.

- [x] **Phase 3 — Port `GET /<code>` (redirect)**
  Ported the redirect lookup (`RedirectResponse`, 302, same `Location` header
  behavior) and its 4 tests. No Redis yet — this phase is Postgres only, to
  keep the FastAPI parity change and the caching change reviewable separately.

  Note for future phases: FastAPI/Starlette matches routes in declaration
  order rather than always preferring static routes over dynamic ones like
  Flask does — `/{code}` is a catch-all and must stay declared *below* every
  static route (`/urls` in Phase 4) in `app/api/routes.py` or it will shadow
  them.

- [x] **Phase 4 — Port `GET /urls`**
  Ported the list endpoint (`URLOut` response model) and its tests, plus a new
  parity test asserting the row shape and `created_at` format are
  byte-identical to Flask's `jsonify()` output (RFC 1123 date string, not
  Pydantic's default ISO 8601 — handled with a `field_serializer`). Declared
  above `/{code}` per the Phase 3 note, and verified against a real `uvicorn`
  server that it isn't shadowed. All 4 endpoints now exist on FastAPI with
  passing tests and the coverage gate intact (97.28%, 46 tests).

- [x] **Phase 5 — Redis caching layer**
  `app/cache.py`: short_code → original_url cache (`REDIS_TTL_SECONDS`,
  default 3600s) sitting in front of the `GET /<code>` Postgres lookup from
  Phase 3. Cache is written on `POST /shorten` and warmed on a Postgres
  fallback after a cache miss. Redis errors are caught and treated as a miss
  — the redirect path falls back to Postgres rather than erroring.

  Caught a real production-latency bug while testing this against a genuinely
  down Redis: redis-py retries on connection failure by default, which turned
  every failed lookup into a ~4.2s stall instead of a fast fallback — enough
  to make an outage worse than no cache at all. Fixed by disabling retries
  (`Retry(NoBackoff(), 0)`, `retry_on_error=[]`) with tight connect/socket
  timeouts (0.5s); confirmed the same failure now resolves in ~3ms.

  New tests: 4 unit tests on the cache module (hit, miss, Redis-down get,
  Redis-down set) + 4 integration tests (shorten warms the cache; a cache hit
  never touches Postgres — enforced by monkeypatching `URL.get` to fail the
  test if called; a cache miss falls back to Postgres and warms the cache;
  a redirect survives Redis being fully down). Also added a `redis` service
  to `.github/workflows/test.yml` so CI can run these — the docker-compose
  service for local/prod still lands in Phase 6.

- [x] **Phase 6 — Infra: docker-compose, env, Dockerfile**
  Added a `redis` service to `docker-compose.yml` (`restart: always`),
  `REDIS_HOST`/`REDIS_PORT`/`REDIS_TTL_SECONDS` to `.env.example`, and
  switched the app container's `CMD` to uvicorn (`run_fastapi:app`). Also
  dropped the obsolete `version:` key.

  Verified by actually bringing up `docker compose up --build` (Postgres +
  Redis + app) and exercising all 4 endpoints through the container network,
  including confirming the redirect's cache key lands in the `redis`
  container itself.

  Two real bugs turned up during that verification, both fixed:
  - No `.dockerignore` existed, so `COPY . .` overwrote the container's
    freshly-built Linux `.venv` with the host's macOS one, forcing `uv` to
    silently rebuild it (and, worse, see the next bug) on every container
    *start* instead of once at build time. Added `.dockerignore`.
  - `.python-version` and `pyproject.toml` both pin Python 3.13, but the
    Dockerfile's base image was `python:3.12-slim` — a mismatch that made
    `uv` download a full CPython 3.13 interpreter from the network on every
    container start. Fixed the base image to `python:3.13-slim`.

  Re-verified `restart: always` actually holds under the FastAPI image:
  killing the process *inside* the container (simulating a real crash, not
  `docker kill` from outside — which Docker treats as an intentional stop
  and deliberately does not auto-restart) recovered in ~0.22s, comfortably
  inside the "2-5 seconds" claim in `docs/FAILURE_MODES.md`.

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
