# Failure Modes

This document describes what happens when different components fail.

## Database Connection Failure

**Symptoms:**
- `POST /shorten` returns 500
- `GET /<code>` returns 500
- `GET /health` returns 200 (health check doesn't verify DB — known limitation)

**Cause:** PostgreSQL is unreachable (crashed, network issue, wrong credentials)

**Recovery:** Restart the database container. The app will automatically reconnect on the next request.

## Short Code Collision

**Probability:** ~1 in 56 billion for 6-character alphanumeric codes

**Behaviour:** App retries up to 5 times before returning a 500 error

**Recovery:** Automatic — no human intervention needed

## App Process Crash

**Behaviour:** Docker's `restart: always` policy automatically restarts the container

**Expected downtime:** 2-5 seconds while Docker detects the crash and restarts

**Recovery:** Automatic

## Invalid Input

**Behaviour:** App returns a 400 JSON error — it does NOT crash

**Recovery:** User corrects their input and retries

## High Traffic / Overload

**Current behaviour:** Single instance — may slow down or time out under heavy load

**Mitigation path:** Add a second app container + Nginx load balancer
