"""Unified response models — same structure returned regardless of forum.

This ensures all scrapers produce identical output shapes,
making the API response predictable for clients.
"""

from pydantic import BaseModel


class Post(BaseModel):
    """Normalized post structure returned by all scrapers."""

    id: str
    title: str
    author: str
    score: int
    upvote_ratio: float
    num_comments: int
    created_utc: float
    url: str
    permalink: str
    selftext: str
    link_flair_text: str
    is_self: bool
    thumbnail: str
