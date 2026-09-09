from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from peewee import IntegrityError

from app.database import db_session
from app.models.url import URL, generate_short_code
from app.schemas import ShortenRequest, ShortenResponse

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
