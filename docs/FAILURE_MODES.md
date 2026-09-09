# Failure Modes

This document describes what happens when different components fail.

## Database Connection Failure

**Symptoms:**
- `POST /shorten` returns 500
- `GET /<code>` returns 500 — *unless the short code is already cached in
  Redis*, in which case the redirect still succeeds (see Redis Cache Failure
  below for the reverse case). A code that's never been looked up since the
  cache was last empty always needs Postgres.
- `GET /urls` returns 500 (not cached — always reads Postgres directly)
- `GET /health` returns 200 (health check doesn't verify DB — known limitation)

**Cause:** PostgreSQL is unreachable (crashed, network issue, wrong credentials)

**Recovery:** Restart the database container. The app will automatically reconnect on the next request.

## Redis Cache Failure

**Symptoms:** None visible to the client. `GET /<code>` still returns the
correct redirect — it just falls back to Postgres on every request instead
of serving from cache, so lookups are slower (see the measured numbers in
`README.md`'s Reliability Features section) until Redis is back.
`POST /shorten` still succeeds; it just can't warm the cache for the new
code.

**Cause:** Redis is unreachable (crashed, network issue, wrong host/port)

**Behaviour:** `app/cache.py` catches any Redis error and treats it as a
cache miss rather than failing the request. Connection/socket timeouts are
capped at 0.5s and retries are disabled, so a down Redis adds milliseconds
to a redirect, not seconds — confirmed by killing Redis under a live
`docker compose` stack and re-measuring `GET /<code>` (see `README.md`).

**Recovery:** Automatic — no human intervention needed. Restart the Redis
container to bring caching back; nothing needs to be replayed since the
cache is repopulated on the next read-through miss or the next `POST /shorten`.

## Short Code Collision

**Probability:** ~1 in 56 billion for 6-character alphanumeric codes

**Behaviour:** App retries up to 5 times before returning a 500 error

**Recovery:** Automatic — no human intervention needed

## App Process Crash

**Behaviour:** Docker's `restart: always` policy automatically restarts the container

**Expected downtime:** A few seconds while Docker detects the crash and
restarts the container. Measured directly against the live FastAPI image by
killing the in-container process (not `docker kill` from outside, which
Docker treats as an intentional stop and deliberately does not
auto-restart): **~0.22s** to `GET /health` responding again. Actual downtime
depends on how fast the process dies and how much work happens at startup
(the app does DB connection init and a `create table if not exists` on
startup) — treat 0.22s as a real observed floor, not a guarantee.

**Recovery:** Automatic

## Invalid Input

**Behaviour:** App returns a 400 JSON error — it does NOT crash

**Recovery:** User corrects their input and retries

## High Traffic / Overload

**Current behaviour:** Single instance — may slow down or time out under heavy load

**Mitigation path:** Add a second app container + Nginx load balancer
