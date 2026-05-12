"""URL and forum name validation utilities.

Generic validators that can be used across all scrapers
for common input validation tasks.
"""

import re
from urllib.parse import urlparse

from core.exceptions import InvalidURLError

# Supported forums for quick validation
SUPPORTED_FORUMS = {"reddit", "producthunt", "stackoverflow", "webmastersun", "quora"}


def validate_url_format(url: str) -> bool:
    """Check if a string is a valid URL with http(s) scheme.

    Args:
        url: The URL string to validate.

    Returns:
        True if the URL is valid.

    Raises:
        InvalidURLError: If the URL format is invalid.
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            raise InvalidURLError("URL must use http or https scheme")
        if not parsed.netloc:
            raise InvalidURLError("URL must have a valid domain")
        return True
    except ValueError:
        raise InvalidURLError("Invalid URL format")


def validate_forum_name(forum: str) -> bool:
    """Check if forum name contains only safe characters.

    Args:
        forum: The forum name to validate.

    Returns:
        True if the name is valid.
    """
    return bool(re.match(r"^[a-zA-Z0-9_-]+$", forum))


def is_supported_forum(forum: str) -> bool:
    """Check if the forum is in the supported list.

    Args:
        forum: Forum name to check.

    Returns:
        True if supported, False otherwise.
    """
    return forum.lower().strip() in SUPPORTED_FORUMS
