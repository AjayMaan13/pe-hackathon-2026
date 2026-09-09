# Error Handling Documentation

This document describes how the API handles errors.

## HTTP Status Codes Used

| Code | Meaning | When it happens |
|------|---------|-----------------|
| 200 | OK | GET /health, GET /urls |
| 201 | Created | POST /shorten succeeds |
| 302 | Found (redirect) | GET /\<code\> when code exists |
| 400 | Bad Request | Missing/invalid input |
| 404 | Not Found | Short code doesn't exist in DB |
| 500 | Internal Server Error | Unexpected server failure |

## 400 Bad Request — When it fires

- Request body is missing entirely
- JSON body doesn't contain a `url` field
- `url` field is an empty string or whitespace only
- `url` doesn't start with `http://` or `https://`

**Response format:**
```json
{
  "error": "URL must start with http:// or https://"
}
```

## 404 Not Found — When it fires

- `GET /<code>` where `code` does not exist in the database

**Response format:**
```json
{
  "error": "Short code 'xyz123' not found"
}
```

## 500 Internal Server Error — When it fires

**Short-code collision** — could not generate a unique short code after 5
attempts (extremely rare, ~1 in 56 billion per attempt):
```json
{
  "error": "Could not generate unique code, try again"
}
```

**Any other unexpected/unhandled error** (e.g. Postgres unreachable) — caught
by a generic exception handler so the request still gets a JSON response
instead of crashing:
```json
{
  "error": "Internal server error"
}
```

## Design Decisions

- All errors return JSON (never HTML crash pages) — enforced by a
  catch-all exception handler on the FastAPI app (`app/fastapi_app.py`),
  not just by the specific error branches above, so this holds even for
  errors nobody anticipated (verified with a test that forces a raw,
  unhandled exception in `POST /shorten` and asserts the response is still
  JSON with no stack trace in the body).
- Error messages are human-readable and describe what went wrong
- No Python stack traces are exposed to the user
- `POST /shorten` validates its body with a Pydantic model
  (`app/schemas.py`); validation failures are converted to the same 400
  JSON shape as the checks above, so the error contract doesn't depend on
  which layer caught the problem
