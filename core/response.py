"""Unified API response models for success and error cases."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response returned by all endpoints."""

    success: bool = False
    forum: str
    error_code: str
    message: str


class SuccessResponse(BaseModel):
    """Standard success response for scrape operations.

    Uses extra='allow' so each forum scraper can add its own fields
    (e.g., 'subreddit' for Reddit, 'product'/'thread' for ProductHunt).
    """

    model_config = ConfigDict(extra="allow")

    success: bool = True
    forum: str
    total_fetched: int
