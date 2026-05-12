"""Product Hunt HTTP fetch logic — fetches forum page HTML and extracts embedded data.

Handles communication with Product Hunt by fetching the forum page
and parsing the Apollo SSR data embedded in the HTML response.
"""

import random
import time

import httpx

from core.config import settings
from core.exceptions import (
    FetchTimeoutError,
    MaxRetriesError,
    PostNotFoundError,
    RateLimitError,
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]


def _get_headers() -> dict[str, str]:
    """Build request headers mimicking a browser."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


def fetch_forum_page(product_slug: str, page: int = 1, sort: str = "") -> str:
    """Fetch a Product Hunt forum page HTML.

    Args:
        product_slug: The product slug (e.g., "zoho").
        page: Page number (1-based). Page 1 has no param, page 2+ uses ?page=N.
        sort: Sort order (trending, popular, featured, new). Empty uses default.

    Returns:
        HTML string of the page.

    Raises:
        PostNotFoundError: If the product/forum is not found (404).
        RateLimitError: If rate limited (429/403).
        MaxRetriesError: If all retries exhausted.
    """
    url = f"https://www.producthunt.com/p/{product_slug}"
    params = {}
    if page > 1:
        params["page"] = page
    if sort:
        params["order"] = sort

    return _request_with_retry(url, params)


def _request_with_retry(url: str, params: dict | None = None) -> str:
    """Execute an HTTP GET request with retry logic.

    Returns:
        HTML response text.
    """
    last_exception = None

    for attempt in range(1, settings.PH_MAX_RETRIES + 1):
        try:
            with httpx.Client(
                timeout=settings.PH_REQUEST_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = client.get(
                    url,
                    params=params,
                    headers=_get_headers(),
                )

            if response.status_code == 200:
                return response.text

            if response.status_code == 429:
                wait = 2 ** attempt + random.uniform(0, 1)
                time.sleep(wait)
                last_exception = RateLimitError("Product Hunt rate limit reached")
                continue

            if response.status_code == 404:
                raise PostNotFoundError("Product Hunt forum not found (404)")

            if response.status_code == 403:
                raise RateLimitError("Product Hunt returned 403 — possible rate limit or blocked")

            last_exception = MaxRetriesError(
                f"Product Hunt returned HTTP {response.status_code}"
            )

        except httpx.TimeoutException:
            last_exception = FetchTimeoutError("Product Hunt request timed out")
            if attempt < settings.PH_MAX_RETRIES:
                time.sleep(3)
        except (PostNotFoundError, RateLimitError):
            raise
        except MaxRetriesError:
            raise
        except Exception as e:
            last_exception = MaxRetriesError(f"Unexpected error: {str(e)}")

    raise last_exception or MaxRetriesError("All retries exhausted for Product Hunt")
