import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.database import db
from app.fastapi_app import create_app as create_fastapi_app
from app.models.url import URL


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def fastapi_client():
    with TestClient(create_fastapi_app()) as client:
        yield client


@pytest.fixture(autouse=True)
def setup_db(app):
    with app.app_context():
        db.create_tables([URL])
        yield
        db.drop_tables([URL])