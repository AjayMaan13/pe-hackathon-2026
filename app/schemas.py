from datetime import datetime

from pydantic import BaseModel, field_serializer, field_validator


class ShortenRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("URL cannot be empty")
        if not value.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return value


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    original_url: str


class URLOut(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: datetime

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime) -> str:
        # Matches Flask/Werkzeug's jsonify() datetime format (RFC 1123, UTC)
        # so GET /urls stays byte-identical for the same DB rows.
        return value.strftime("%a, %d %b %Y %H:%M:%S GMT")
