import pytest
from fastapi.testclient import TestClient

from app.fastapi_app import create_app


@pytest.fixture
def fastapi_client():
    with TestClient(create_app()) as client:
        yield client


# 2 Tests
class TestFastAPIHealthEndpoint:

    def test_health_returns_200(self, fastapi_client):
        assert fastapi_client.get("/health").status_code == 200

    def test_health_returns_ok_status(self, fastapi_client):
        assert fastapi_client.get("/health").json()["status"] == "ok"
