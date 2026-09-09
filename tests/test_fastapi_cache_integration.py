from app import cache
from app.database import db_session
from app.models.url import URL


# 4 Tests
class TestFastAPICacheIntegration:

    def test_shorten_warms_cache(self, fastapi_client):
        data = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()
        assert cache.get_cached_url(data["short_code"]) == "https://google.com"

    def test_redirect_hits_cache_without_querying_postgres(self, fastapi_client, monkeypatch):
        code = fastapi_client.post("/shorten", json={"url": "https://google.com"}).json()["short_code"]

        def _fail_if_called(*args, **kwargs):
            raise AssertionError("Postgres should not be queried on a cache hit")

        monkeypatch.setattr(URL, "get", _fail_if_called)

        response = fastapi_client.get(f"/{code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"] == "https://google.com"

    def test_redirect_falls_back_to_postgres_on_cache_miss_and_warms_cache(self, fastapi_client):
        with db_session():
            url_record = URL.create(original_url="https://github.com", short_code="ghmiss")

        assert cache.get_cached_url(url_record.short_code) is None

        response = fastapi_client.get(f"/{url_record.short_code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"] == "https://github.com"
        assert cache.get_cached_url(url_record.short_code) == "https://github.com"

    def test_redirect_survives_redis_down(self, fastapi_client, monkeypatch):
        with db_session():
            url_record = URL.create(original_url="https://example.com", short_code="rdown1")

        monkeypatch.setattr(cache, "_client", None)
        monkeypatch.setenv("REDIS_PORT", "1")

        response = fastapi_client.get(f"/{url_record.short_code}", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["Location"] == "https://example.com"
