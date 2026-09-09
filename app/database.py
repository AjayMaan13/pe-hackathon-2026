import os
from contextlib import contextmanager

from peewee import DatabaseProxy, Model, PostgresqlDatabase

db = DatabaseProxy()


class BaseModel(Model):
    class Meta:
        database = db


def _build_database():
    return PostgresqlDatabase(
        os.environ.get("DATABASE_NAME", "hackathon_db"),
        host=os.environ.get("DATABASE_HOST", "localhost"),
        port=int(os.environ.get("DATABASE_PORT", 5432)),
        user=os.environ.get("DATABASE_USER", "postgres"),
        password=os.environ.get("DATABASE_PASSWORD", "postgres"),
    )


def init_peewee_db():
    """Initialize the shared Peewee DatabaseProxy. Safe to call once at
    startup by any web framework wiring this app together."""
    db.initialize(_build_database())


def init_db(app):
    init_peewee_db()

    @app.before_request
    def _db_connect():
        db.connect(reuse_if_open=True)

    @app.teardown_appcontext
    def _db_close(exc):
        if not db.is_closed():
            db.close()


@contextmanager
def db_session():
    """Connect/close around a single sync call. Peewee's connection state
    is thread-local, and FastAPI's threadpool does not guarantee a request's
    dependencies and endpoint body share a thread — so this must be entered
    and exited from inside the same sync route function, not from ASGI
    middleware."""
    db.connect(reuse_if_open=True)
    try:
        yield
    finally:
        if not db.is_closed():
            db.close()
