from app import cache


# 4 Tests
class TestCacheModule:

    def test_set_then_get_returns_value(self):
        cache.set_cached_url("abc123", "https://example.com")
        assert cache.get_cached_url("abc123") == "https://example.com"

    def test_get_missing_key_returns_none(self):
        assert cache.get_cached_url("doesnotexist") is None

    def test_redis_down_get_returns_none(self, monkeypatch):
        monkeypatch.setattr(cache, "_client", None)
        monkeypatch.setenv("REDIS_PORT", "1")
        assert cache.get_cached_url("abc123") is None

    def test_redis_down_set_does_not_raise(self, monkeypatch):
        monkeypatch.setattr(cache, "_client", None)
        monkeypatch.setenv("REDIS_PORT", "1")
        cache.set_cached_url("abc123", "https://example.com")
