from app.models.url import generate_short_code

# 5 Tests
class TestGenerateShortCode:

    def test_default_length_is_6(self):
        code = generate_short_code()
        assert len(code) == 6

    def test_custom_length(self):
        code = generate_short_code(length=10)
        assert len(code) == 10

    def test_is_alphanumeric(self):
        code = generate_short_code()
        assert code.isalnum()

    def test_codes_are_different(self):
        assert generate_short_code() != generate_short_code()

    def test_zero_length(self):
        assert generate_short_code(length=0) == ""

# 2 Tests
class TestHealthEndpoint:

    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_returns_ok_status(self, client):
        assert client.get("/health").get_json()["status"] == "ok"

# 9 Tests
class TestShortenEndpoint:

    def test_shorten_valid_url_returns_201(self, client):
        assert client.post("/shorten", json={"url": "https://google.com"}).status_code == 201

    def test_shorten_returns_short_code(self, client):
        data = client.post("/shorten", json={"url": "https://google.com"}).get_json()
        assert "short_code" in data
        assert len(data["short_code"]) == 6

    def test_shorten_returns_original_url(self, client):
        data = client.post("/shorten", json={"url": "https://google.com"}).get_json()
        assert data["original_url"] == "https://google.com"

    def test_shorten_missing_url_field_returns_400(self, client):
        assert client.post("/shorten", json={"foo": "bar"}).status_code == 400

    def test_shorten_empty_url_returns_400(self, client):
        assert client.post("/shorten", json={"url": ""}).status_code == 400

    def test_shorten_no_body_returns_400(self, client):
        assert client.post("/shorten").status_code == 400

    def test_shorten_invalid_url_no_protocol_returns_400(self, client):
        assert client.post("/shorten", json={"url": "google.com"}).status_code == 400

    def test_shorten_http_url_accepted(self, client):
        assert client.post("/shorten", json={"url": "http://example.com"}).status_code == 201

    def test_two_different_urls_get_different_codes(self, client):
        r1 = client.post("/shorten", json={"url": "https://google.com"}).get_json()
        r2 = client.post("/shorten", json={"url": "https://github.com"}).get_json()
        assert r1["short_code"] != r2["short_code"]

# 4 Tests
class TestRedirectEndpoint:

    def test_valid_code_redirects(self, client):
        code = client.post("/shorten", json={"url": "https://google.com"}).get_json()["short_code"]
        assert client.get(f"/{code}").status_code == 302

    def test_valid_code_redirects_to_correct_url(self, client):
        code = client.post("/shorten", json={"url": "https://google.com"}).get_json()["short_code"]
        assert "google.com" in client.get(f"/{code}").headers["Location"]

    def test_invalid_code_returns_404(self, client):
        assert client.get("/definitelynotacode").status_code == 404

    def test_invalid_code_returns_json_error(self, client):
        data = client.get("/doesnotexist").get_json()
        assert data is not None
        assert "error" in data

# 3 Tests
class TestListEndpoint:

    def test_list_returns_200(self, client):
        assert client.get("/urls").status_code == 200

    def test_list_empty_when_no_urls(self, client):
        assert client.get("/urls").get_json() == []

    def test_list_shows_created_url(self, client):
        client.post("/shorten", json={"url": "https://example.com"})
        data = client.get("/urls").get_json()
        assert len(data) == 1
        assert data[0]["original_url"] == "https://example.com"