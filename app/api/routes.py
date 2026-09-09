from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse
from peewee import IntegrityError

from app.database import db_session
from app.models.url import URL, generate_short_code
from app.schemas import ShortenRequest, ShortenResponse, URLOut

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/shorten", response_model=ShortenResponse, status_code=201)
def shorten_url(payload: ShortenRequest, request: Request):
    with db_session():
        for _ in range(5):
            short_code = generate_short_code()
            try:
                url_record = URL.create(original_url=payload.url, short_code=short_code)
                return ShortenResponse(
                    short_code=url_record.short_code,
                    short_url=f"{request.base_url}{url_record.short_code}",
                    original_url=url_record.original_url,
                )
            except IntegrityError:
                continue

        return JSONResponse(
            status_code=500,
            content={"error": "Could not generate unique code, try again"},
        )


@router.get("/urls", response_model=list[URLOut])
def list_urls():
    with db_session():
        urls = URL.select().order_by(URL.created_at.desc())
        return [
            URLOut(
                id=u.id,
                original_url=u.original_url,
                short_code=u.short_code,
                created_at=u.created_at,
            )
            for u in urls
        ]


# Catch-all path param: unlike Flask, FastAPI/Starlette matches routes in
# declaration order rather than always preferring static routes, so this
# must stay declared below every static route (e.g. /urls) or it will
# shadow them.
@router.get("/{code}")
def redirect_to_url(code: str):
    with db_session():
        try:
            url_record = URL.get(URL.short_code == code)
        except URL.DoesNotExist:
            return JSONResponse(status_code=404, content={"error": f"Short code '{code}' not found"})

        return RedirectResponse(url=url_record.original_url, status_code=302)
