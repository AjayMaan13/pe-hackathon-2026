import pytest
from pydantic import ValidationError

from app.schemas import ShortenRequest, ShortenResponse


# 3 Tests
class TestShortenRequest:

    def test_accepts_url_field(self):
        assert ShortenRequest(url="https://example.com").url == "https://example.com"

    def test_missing_url_field_raises(self):
        with pytest.raises(ValidationError):
            ShortenRequest()


class TestShortenResponse:

    def test_serializes_expected_fields(self):
        response = ShortenResponse(
            short_code="aB3xZ9",
            short_url="http://localhost:8080/aB3xZ9",
            original_url="https://example.com",
        )
        assert response.model_dump() == {
            "short_code": "aB3xZ9",
            "short_url": "http://localhost:8080/aB3xZ9",
            "original_url": "https://example.com",
        }
