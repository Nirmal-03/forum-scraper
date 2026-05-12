"""WebmasterSun URL validation.

Supports URL pattern:
- https://www.webmastersun.com/search/{search_id}/?q={query}&o=date
"""

import re
from urllib.parse import urlparse, parse_qs

from core.exceptions import InvalidURLError

# Pattern: /search/{id}/
SEARCH_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?webmastersun\.com/search/(\d+)/",
    re.IGNORECASE,
)


def validate_webmastersun_url(url: str) -> dict:
    """Validate a WebmasterSun search URL and extract components.

    Args:
        url: The URL to validate.

    Returns:
        Dict with search_id and base_url (without page param).

    Raises:
        InvalidURLError: If the URL format is invalid.
    """
    match = SEARCH_URL_PATTERN.match(url)
    if not match:
        raise InvalidURLError(
            "Invalid WebmasterSun URL. Expected format:\n"
            "  - https://www.webmastersun.com/search/{id}/?q={query}"
        )

    search_id = match.group(1)

    # Parse and rebuild base URL without page param
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    # Remove page param if present — we handle pagination ourselves
    params.pop("page", None)

    # Rebuild query string without page
    query_parts = []
    for key, values in params.items():
        for val in values:
            query_parts.append(f"{key}={val}")
    base_query = "&".join(query_parts)

    base_url = f"https://www.webmastersun.com/search/{search_id}/"
    if base_query:
        base_url += f"?{base_query}"

    return {
        "search_id": search_id,
        "base_url": base_url,
        "query": params.get("q", [""])[0],
    }
