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

    @app.middleware("http")
    async def _peewee_connection(request: Request, call_next):
        db.connect(reuse_if_open=True)
        try:
            return await call_next(request)
        finally:
            if not db.is_closed():
                db.close()

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"error": "Invalid request body"})

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(request: Request, exc: Exception):
        return JSONResponse(status_code=500, content={"error": "Internal server error"})

    app.include_router(router)

    return app
