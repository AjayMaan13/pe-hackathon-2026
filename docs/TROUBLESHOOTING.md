# Troubleshooting

## Connection refused on startup
**Symptom:** `connection refused` when starting the app  
**Fix:** PostgreSQL isn't running. Start it first:
```bash
docker compose up db
# then wait a few seconds, then:
docker compose up app
```

## "relation urls does not exist"
**Symptom:** 500 errors on every request  
**Fix:** Tables haven't been created yet. Run once after the DB is up:
```bash
uv run python setup_db.py
```

## Tests fail locally but pass in CI
**Symptom:** Tests pass in GitHub Actions but fail on your machine  
**Fix:** Your local `.env` credentials don't match CI defaults. Confirm:
```
DATABASE_HOST=localhost
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
```

## Port already in use
**Symptom:** `address already in use` on port 8081  
**Fix:** Find and kill the process using it:
```bash
lsof -i :8081
kill <PID>
```
Or change the port mapping in `docker-compose.yml`.

## Coverage drops below 50% in CI
**Symptom:** CI fails on the coverage step  
**Fix:** You added code without tests. Find uncovered lines:
```bash
uv run pytest --cov=app --cov-report=term-missing
```
