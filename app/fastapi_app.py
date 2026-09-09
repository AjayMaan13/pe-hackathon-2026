from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import router
from app.database import db, init_peewee_db


@asynccontextmanager
async def _lifespan(app: FastAPI):
    init_peewee_db()

    from app.models.url import URL
    db.create_tables([URL], safe=True)

    yield


def create_app() -> FastAPI:
    load_dotenv()

    app = FastAPI(title="URL Shortener", lifespan=_lifespan)

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        custom_error = errors[0].get("ctx", {}).get("error") if errors else None
        message = str(custom_error) if custom_error is not None else "Missing 'url' field in request body"
        return JSONResponse(status_code=400, content={"error": message})

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    app.include_router(router)

    return app
