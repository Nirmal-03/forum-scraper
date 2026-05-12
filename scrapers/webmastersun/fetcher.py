"""WebmasterSun HTTP fetch logic — fetches search result pages.

Scrapes the XenForo-based search results by fetching HTML pages.
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


def fetch_search_page(base_url: str, page: int = 1) -> str:
    """Fetch a WebmasterSun search results page.

    Args:
        base_url: The base search URL (without page param).
        page: Page number (1-based).

    Returns:
        HTML string of the page.

    Raises:
        PostNotFoundError: If search not found (404).
        RateLimitError: If rate limited.
        MaxRetriesError: If all retries exhausted.
    """
    # Build URL with page param
    if page > 1:
        separator = "&" if "?" in base_url else "?"
        url = f"{base_url}{separator}page={page}"
    else:
        url = base_url

    return _request_with_retry(url)


def fetch_post_page(url: str) -> str:
    """Fetch a WebmasterSun thread/post page to get full content.

    Args:
        url: Full URL to the specific post (e.g. /threads/.../post-XXXXX).

    Returns:
        HTML string of the thread page.
    """
    return _request_with_retry(url)


def _request_with_retry(url: str) -> str:
    """Execute an HTTP GET request with retry logic.

    Returns:
        HTML response text.
    """
    last_exception = None

    for attempt in range(1, settings.WMS_MAX_RETRIES + 1):
        try:
            with httpx.Client(
                timeout=settings.WMS_REQUEST_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = client.get(url, headers=_get_headers())

                if response.status_code == 200:
                    return response.text

                if response.status_code == 404:
                    raise PostNotFoundError("Search not found on WebmasterSun")

                if response.status_code in (429, 403):
                    wait = attempt * 5
                    time.sleep(wait)
                    last_exception = RateLimitError(
                        f"Rate limited by WebmasterSun (attempt {attempt})"
                    )
                    continue

                last_exception = Exception(
                    f"WebmasterSun returned {response.status_code}"
                )

        except httpx.TimeoutException:
            last_exception = FetchTimeoutError("WebmasterSun request timed out")
        except (PostNotFoundError, RateLimitError):
            raise
        except httpx.HTTPError as e:
            last_exception = FetchTimeoutError(f"HTTP error: {str(e)}")

        if attempt < settings.WMS_MAX_RETRIES:
            time.sleep(attempt * 2)

    raise MaxRetriesError(
        f"Failed after {settings.WMS_MAX_RETRIES} attempts: {last_exception}"
    )
