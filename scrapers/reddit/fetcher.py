"""Reddit HTTP fetch logic — safe requests with retry and header rotation.

Handles all HTTP communication with Reddit's JSON API including:
- User-Agent rotation
- Retry with exponential backoff on 429
- Proper error classification
"""

import random
import time

import httpx

from core.config import settings
from core.exceptions import (
    FetchTimeoutError,
    MaxRetriesError,
    PostNotFoundError,
    PrivatePostError,
    RateLimitError,
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
]


def _get_headers() -> dict[str, str]:
    """Build request headers with a randomly selected User-Agent."""
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def fetch_subreddit_posts(subreddit: str, sort: str = "hot", after: str | None = None, limit: int = 100) -> dict:
    """Fetch posts from a subreddit listing.

    Args:
        subreddit: The subreddit name (e.g., "Zoho").
        sort: Sort order (hot, new, top, rising).
        after: Pagination cursor (fullname of last item, e.g., "t3_abc123").
        limit: Number of posts per page (max 100 per Reddit API).

    Returns:
        Parsed JSON response dict.

    Raises:
        PostNotFoundError: If subreddit returns 404.
        PrivatePostError: If subreddit is private (403).
        MaxRetriesError: If all retries fail.
    """
    url = f"{settings.REDDIT_BASE_URL}/r/{subreddit}/{sort}.json"
    params = {"limit": min(limit, 100)}
    if after:
        params["after"] = after

    return _request_with_retry("GET", url, params=params)


def _request_with_retry(method: str, url: str, params: dict | None = None) -> list | dict:
    """Execute an HTTP request with retry logic.

    Retries on 429 (rate limit) with exponential backoff.
    Retries on timeout with fixed 5-second wait.
    Does NOT retry on 403/404 — raises immediately.

    Args:
        method: HTTP method (GET/POST).
        url: Target URL.
        params: Query parameters or form data.

    Returns:
        Parsed JSON response.
    """
    last_exception = None

    for attempt in range(1, settings.REDDIT_MAX_RETRIES + 1):
        try:
            with httpx.Client(
                timeout=settings.REDDIT_REQUEST_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = client.request(
                    method=method,
                    url=url,
                    params=params if method == "GET" else None,
                    data=params if method == "POST" else None,
                    headers=_get_headers(),
                )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 403:
                raise PrivatePostError("This subreddit is private or restricted")

            if response.status_code == 404:
                raise PostNotFoundError("Subreddit not found")

            if response.status_code == 429:
                wait_time = attempt * 10
                time.sleep(wait_time)
                last_exception = RateLimitError(f"Rate limited, waited {wait_time}s (attempt {attempt})")
                continue

            # Other errors — retry
            last_exception = Exception(f"HTTP {response.status_code}")
            time.sleep(5)

        except (PrivatePostError, PostNotFoundError):
            raise
        except httpx.TimeoutException:
            last_exception = FetchTimeoutError("Reddit did not respond in time")
            time.sleep(5)
        except (httpx.RequestError, Exception) as e:
            if isinstance(e, (PrivatePostError, PostNotFoundError, FetchTimeoutError)):
                raise
            last_exception = e
            time.sleep(5)

    if isinstance(last_exception, FetchTimeoutError):
        raise last_exception
    raise MaxRetriesError("Failed after maximum retry attempts")
