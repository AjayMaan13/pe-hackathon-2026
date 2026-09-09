import re

# 4 Tests
class TestFastAPIListEndpoint:

    def test_list_returns_200(self, fastapi_client):
        assert fastapi_client.get("/urls").status_code == 200

    def test_list_empty_when_no_urls(self, fastapi_client):
        assert fastapi_client.get("/urls").json() == []

    def test_list_shows_created_url(self, fastapi_client):
        fastapi_client.post("/shorten", json={"url": "https://example.com"})
        data = fastapi_client.get("/urls").json()
        assert len(data) == 1
        assert data[0]["original_url"] == "https://example.com"

    def test_list_row_shape_matches_flask_contract(self, fastapi_client):
        fastapi_client.post("/shorten", json={"url": "https://example.com"})
        row = fastapi_client.get("/urls").json()[0]

        assert set(row.keys()) == {"id", "original_url", "short_code", "created_at"}
        # RFC 1123, matching Flask/Werkzeug's jsonify() datetime format
        assert re.fullmatch(r"\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT", row["created_at"])
