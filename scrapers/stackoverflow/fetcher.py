"""Stack Overflow HTTP fetch logic — calls the SE API v2.3.

Uses the official Stack Exchange API with an API key for higher quota.
Responses are JSON with gzip compression handled by httpx.
"""

import time

import httpx

from core.config import settings
from core.exceptions import (
    FetchTimeoutError,
    MaxRetriesError,
    PostNotFoundError,
    RateLimitError,
)


def fetch_questions(
    tag: str,
    sort: str = "activity",
    page: int = 1,
    pagesize: int = 100,
) -> dict:
    """Fetch questions from Stack Overflow by tag.

    Args:
        tag: The tag to filter by (e.g., "zohobooks").
        sort: Sort order (activity, votes, creation, hot, week, month).
        page: Page number (1-based).
        pagesize: Number of results per page (max 100).

    Returns:
        Parsed JSON response dict.

    Raises:
        PostNotFoundError: If tag not found or no results.
        RateLimitError: If rate limited (backoff).
        MaxRetriesError: If all retries exhausted.
        FetchTimeoutError: If request times out.
    """
    params = {
        "site": "stackoverflow",
        "tagged": tag,
        "sort": sort,
        "order": "desc",
        "page": page,
        "pagesize": min(pagesize, 100),
        "filter": "withbody",
    }

    if settings.SO_API_KEY:
        params["key"] = settings.SO_API_KEY

    return _request_with_retry(f"{settings.SO_BASE_URL}/questions", params)


def _request_with_retry(url: str, params: dict) -> dict:
    """Execute an HTTP GET with retry logic for SO API.

    Returns:
        Parsed JSON response.
    """
    last_exception = None

    for attempt in range(1, settings.SO_MAX_RETRIES + 1):
        try:
            with httpx.Client(
                timeout=settings.SO_REQUEST_TIMEOUT,
                follow_redirects=True,
            ) as client:
                response = client.get(url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    # SO API returns backoff field if we should slow down
                    if "backoff" in data:
                        time.sleep(data["backoff"])
                    return data

                if response.status_code == 400:
                    error_data = response.json()
                    msg = error_data.get("error_message", "Bad request")
                    raise PostNotFoundError(f"Stack Overflow: {msg}")

                if response.status_code == 429 or response.status_code == 502:
                    wait = attempt * 5
                    time.sleep(wait)
                    last_exception = RateLimitError(
                        f"Rate limited by Stack Overflow (attempt {attempt})"
                    )
                    continue

                if response.status_code == 404:
                    raise PostNotFoundError("Tag not found on Stack Overflow")

                # Other errors
                last_exception = Exception(
                    f"SO API returned {response.status_code}"
                )

        except httpx.TimeoutException:
            last_exception = FetchTimeoutError("Stack Overflow API request timed out")
        except (PostNotFoundError, RateLimitError):
            raise
        except httpx.HTTPError as e:
            last_exception = FetchTimeoutError(f"HTTP error: {str(e)}")

        if attempt < settings.SO_MAX_RETRIES:
            time.sleep(attempt * 2)

    raise MaxRetriesError(
        f"Failed after {settings.SO_MAX_RETRIES} attempts: {last_exception}"
    )
