"""Quora URL validation.

Supports URL pattern:
- https://www.quora.com/topic/{slug}/
- https://quora.com/topic/{slug}
"""

import re

from core.exceptions import InvalidURLError

TOPIC_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?quora\.com/topic/([a-zA-Z0-9_-]+)",
    re.IGNORECASE,
)


def validate_quora_url(url: str) -> dict:
    """Validate a Quora topic URL and extract the slug.

    Args:
        url: The URL to validate.

    Returns:
        Dict with topic_slug and normalized url.

    Raises:
        InvalidURLError: If the URL format is invalid.
    """
    match = TOPIC_URL_PATTERN.match(url)
    if not match:
        raise InvalidURLError(
            "Invalid Quora URL. Expected format:\n"
            "  - https://www.quora.com/topic/{topic-slug}"
        )

    topic_slug = match.group(1)
    normalized_url = f"https://www.quora.com/topic/{topic_slug}"

    return {
        "topic_slug": topic_slug,
        "url": normalized_url,
    }
