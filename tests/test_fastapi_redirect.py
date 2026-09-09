# 4 Tests
class TestFastAPIRedirectEndpoint:

    def test_valid_code_redirects(self, fastapi_client):
        code = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()["short_code"]
        response = fastapi_client.get(f"/{code}", follow_redirects=False)
        assert response.status_code == 302

    def test_valid_code_redirects_to_correct_url(self, fastapi_client):
        code = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()["short_code"]
        response = fastapi_client.get(f"/{code}", follow_redirects=False)
        assert "google.com" in response.headers["Location"]

    def test_invalid_code_returns_404(self, fastapi_client):
        assert fastapi_client.get("/definitelynotacode", follow_redirects=False).status_code == 404

    def test_invalid_code_returns_json_error(self, fastapi_client):
        response = fastapi_client.get("/doesnotexist", follow_redirects=False)
        data = response.json()
        assert data is not None
        assert "error" in data
