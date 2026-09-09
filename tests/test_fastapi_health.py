# 2 Tests
class TestFastAPIHealthEndpoint:

    def test_health_returns_200(self, fastapi_client):
        assert fastapi_client.get("/health").status_code == 200

    def test_health_returns_ok_status(self, fastapi_client):
        assert fastapi_client.get("/health").json()["status"] == "ok"
