"""Reusable HTTP utilities — safe request wrapper, random delay, User-Agent rotation.

These utilities can be shared across multiple scrapers.
"""

import random
import time

import httpx

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
]


def get_random_user_agent() -> str:
    """Return a randomly selected User-Agent string."""
    return random.choice(USER_AGENTS)


def get_default_headers() -> dict[str, str]:
    """Build default request headers with rotated User-Agent."""
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }


def random_delay(min_sec: float = 1.5, max_sec: float = 3.5) -> None:
    """Sleep for a random duration to mimic human behavior.

    Args:
        min_sec: Minimum delay in seconds.
        max_sec: Maximum delay in seconds.
    """
    time.sleep(random.uniform(min_sec, max_sec))


def safe_request(
    method: str,
    url: str,
    params: dict | None = None,
    timeout: int = 10,
    headers: dict | None = None,
) -> httpx.Response:
    """Make an HTTP request with default headers and timeout.

    Args:
        method: HTTP method (GET, POST, etc.).
        url: Target URL.
        params: Query parameters.
        timeout: Request timeout in seconds.
        headers: Optional custom headers (merged with defaults).

    Returns:
        The httpx Response object.

    Raises:
        httpx.TimeoutException: If the request times out.
        httpx.RequestError: On connection issues.
    """
    request_headers = get_default_headers()
    if headers:
        request_headers.update(headers)

    with httpx.Client(timeout=timeout) as client:
        response = client.request(
            method=method,
            url=url,
            params=params if method.upper() == "GET" else None,
            data=params if method.upper() == "POST" else None,
            headers=request_headers,
        )

    return response
