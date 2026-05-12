"""Product Hunt URL validation and slug extraction.

Supports URL patterns:
- https://www.producthunt.com/p/{product_slug}
- https://www.producthunt.com/products/{product_slug}
"""

import re
from urllib.parse import urlparse

from core.exceptions import InvalidURLError

# Pattern: /p/{slug}
FORUM_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?producthunt\.com/p/([a-zA-Z0-9_-]+)/?$",
    re.IGNORECASE,
)

# Pattern: /products/{slug}
PRODUCTS_URL_PATTERN = re.compile(
    r"https?://(?:www\.)?producthunt\.com/products/([a-zA-Z0-9_-]+)/?$",
    re.IGNORECASE,
)


def validate_producthunt_url(url: str) -> str:
    """Validate a Product Hunt URL and extract the product/forum slug.

    Args:
        url: The Product Hunt URL to validate.

    Returns:
        The product slug (e.g., "zoho").

    Raises:
        InvalidURLError: If URL is not a valid Product Hunt forum/product URL.
    """
    url = url.strip().rstrip("/")

    # Strip query parameters before matching
    parsed = urlparse(url)
    url = parsed._replace(query="", fragment="").geturl().rstrip("/")

    # Try /p/{slug} pattern
    match = FORUM_URL_PATTERN.match(url + "/")
    if match:
        return match.group(1)

    # Try /products/{slug} pattern
    match = PRODUCTS_URL_PATTERN.match(url + "/")
    if match:
        return match.group(1)

    raise InvalidURLError(
        "Invalid Product Hunt URL. Supported formats:\n"
        "  - https://www.producthunt.com/p/{product}\n"
        "  - https://www.producthunt.com/products/{product}"
    )
