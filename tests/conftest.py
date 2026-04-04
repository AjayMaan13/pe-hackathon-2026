import pytest

from app import create_app
from app.database import db
from app.models.url import URL


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def setup_db(app):
    with app.app_context():
        db.create_tables([URL])
        yield
        db.drop_tables([URL])