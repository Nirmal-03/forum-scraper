"""Common request models for the scrape endpoint.

These models define the contract that all forum requests must follow.
Forum-specific options are nested inside the optional `options` field.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ScrapeRequest(BaseModel):
    """Request body for the POST /api/v1/scrape endpoint."""

    forum: str = Field(..., description="Which forum to scrape (e.g., 'reddit')")
    url: str = Field(..., description="The post/thread URL to scrape")
    limit: int = Field(default=100, ge=1, le=10000, description="Max comments to fetch")
    options: dict[str, Any] | None = Field(default=None, description="Forum-specific options")

    @field_validator("forum")
    @classmethod
    def validate_forum_not_empty(cls, v: str) -> str:
        """Ensure forum name is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Forum name cannot be empty")
        return v.strip().lower()

    @field_validator("url")
    @classmethod
    def validate_url_not_empty(cls, v: str) -> str:
        """Ensure URL is not empty or whitespace."""
        if not v.strip():
            raise ValueError("URL cannot be empty")
        return v.strip()
