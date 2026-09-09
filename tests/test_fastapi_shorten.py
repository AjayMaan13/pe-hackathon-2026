# 10 Tests
class TestFastAPIShortenEndpoint:

    def test_shorten_valid_url_returns_201(self, fastapi_client):
        assert fastapi_client.post("/shorten", json={"url": "https://google.com"}).status_code == 201

    def test_shorten_returns_short_code(self, fastapi_client):
        data = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()
        assert "short_code" in data
        assert len(data["short_code"]) == 6

    def test_shorten_returns_original_url(self, fastapi_client):
        data = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()
        assert data["original_url"] == "https://google.com"

    def test_shorten_missing_url_field_returns_400(self, fastapi_client):
        assert fastapi_client.post("/shorten", json={"foo": "bar"}).status_code == 400

    def test_shorten_empty_url_returns_400(self, fastapi_client):
        assert fastapi_client.post("/shorten", json={"url": ""}).status_code == 400

    def test_shorten_no_body_returns_400(self, fastapi_client):
        assert fastapi_client.post("/shorten").status_code == 400

    def test_shorten_invalid_url_no_protocol_returns_400(self, fastapi_client):
        assert fastapi_client.post("/shorten", json={"url": "google.com"}).status_code == 400

    def test_shorten_http_url_accepted(self, fastapi_client):
        assert fastapi_client.post("/shorten", json={"url": "http://example.com"}).status_code == 201

    def test_two_different_urls_get_different_codes(self, fastapi_client):
        r1 = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()
        r2 = fastapi_client.post("/shorten", json={"url": "https://github.com"}).json()
        assert r1["short_code"] != r2["short_code"]

    def test_unexpected_db_error_returns_500_json_no_stack_trace(self, monkeypatch):
        from fastapi.testclient import TestClient

        from app.fastapi_app import create_app
        from app.models.url import URL

        def _boom(*args, **kwargs):
            raise RuntimeError("connection refused")

        monkeypatch.setattr(URL, "create", _boom)

        # raise_server_exceptions=False: assert on the actual HTTP response a
        # real client gets, not the exception TestClient re-raises by default
        # after the ASGI response has already been sent.
        with TestClient(create_app(), raise_server_exceptions=False) as client:
            response = client.post("/shorten", json={"url": "https://google.com"})

        assert response.status_code == 500
        assert response.json() == {"error": "Internal server error"}
        assert "RuntimeError" not in response.text
        assert "Traceback" not in response.text
