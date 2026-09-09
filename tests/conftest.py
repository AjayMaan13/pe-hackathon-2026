import pytest
import redis
from fastapi.testclient import TestClient

from app.cache import _get_client as _get_redis_client
from app.database import db, init_peewee_db
from app.fastapi_app import create_app as create_fastapi_app
from app.models.url import URL


@pytest.fixture
def fastapi_client():
    with TestClient(create_fastapi_app()) as client:
        yield client


@pytest.fixture(autouse=True)
def setup_db():
    init_peewee_db()
    db.create_tables([URL])
    yield
    db.drop_tables([URL])


@pytest.fixture(autouse=True)
def flush_cache():
    try:
        _get_redis_client().flushdb()
    except redis.RedisError:
        pass
    yield
