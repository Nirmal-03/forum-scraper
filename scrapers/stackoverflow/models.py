"""Stack Overflow URL validation and tag extraction.

Supports URL pattern:
- https://stackoverflow.com/questions/tagged/zohobooks
"""

import re

from core.exceptions import InvalidURLError

# Pattern: /questions/tagged/{tag}
TAGGED_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?stackoverflow\.com/questions/tagged/([a-zA-Z0-9_.+-]+)/?(\?.*)?$",
    re.IGNORECASE,
)


def validate_stackoverflow_url(url: str) -> str:
    """Validate a Stack Overflow tagged URL and extract the tag.

    Args:
        url: The URL to validate.

    Returns:
        The tag string.

    Raises:
        InvalidURLError: If the URL format is invalid.
    """
    match = TAGGED_URL_PATTERN.match(url)
    if not match or not match.group(1):
        raise InvalidURLError(
            "Invalid Stack Overflow URL. Expected format:\n"
            "  - https://stackoverflow.com/questions/tagged/{tag}"
        )

    return match.group(1)
