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

- Could not generate a unique short code after 5 attempts (extremely rare)
- Unexpected database error

**Response format:**
```json
{
  "error": "Could not generate unique code, try again"
}
```

## Design Decisions

- All errors return JSON (never HTML crash pages)
- Error messages are human-readable and describe what went wrong
- No Python stack traces are exposed to the user
