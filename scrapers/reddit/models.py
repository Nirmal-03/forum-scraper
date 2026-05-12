"""Reddit-specific input validation models."""

import re

from core.exceptions import InvalidURLError

# Matches Reddit subreddit URLs: /r/Name/ or /r/Name
REDDIT_SUBREDDIT_URL_PATTERN = re.compile(
    r"https?://(www\.|old\.|new\.)?reddit\.com/r/([a-zA-Z0-9_]+)/?(\?.*)?$",
    re.IGNORECASE,
)


def validate_subreddit_url(url: str) -> str:
    """Validate that the URL is a valid subreddit URL and extract subreddit name.

    Args:
        url: The URL to validate.

    Returns:
        The subreddit name.

    Raises:
        InvalidURLError: If the URL is not a valid subreddit URL.
    """
    match = REDDIT_SUBREDDIT_URL_PATTERN.match(url)
    if not match or not match.group(2):
        raise InvalidURLError("The provided URL is not a valid Reddit subreddit URL")

    return match.group(2)
