"""Custom exception classes for the Forum Scraper application.

All exceptions inherit from ForumScraperBaseError to allow
unified exception handling at the API layer.
"""


class ForumScraperBaseError(Exception):
    """Base exception for all forum scraper errors."""

    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)


class UnsupportedForumError(ForumScraperBaseError):
    """Raised when an unsupported forum name is provided."""

    def __init__(self, forum: str):
        super().__init__(
            message=f"Forum '{forum}' is not supported",
            error_code="UNSUPPORTED_FORUM",
            status_code=400,
        )


class InvalidURLError(ForumScraperBaseError):
    """Raised when the URL format is invalid for the target forum."""

    def __init__(self, message: str = "Invalid URL format"):
        super().__init__(
            message=message,
            error_code="INVALID_URL",
            status_code=400,
        )



class PrivatePostError(ForumScraperBaseError):
    """Raised when the post is private or restricted."""

    def __init__(self, message: str = "This post is private or restricted"):
        super().__init__(
            message=message,
            error_code="PRIVATE_POST",
            status_code=403,
        )


class PostNotFoundError(ForumScraperBaseError):
    """Raised when the post does not exist or was deleted."""

    def __init__(self, message: str = "Post not found"):
        super().__init__(
            message=message,
            error_code="POST_NOT_FOUND",
            status_code=404,
        )


class RateLimitError(ForumScraperBaseError):
    """Raised when rate limited by the forum platform."""

    def __init__(self, message: str = "Rate limited — retrying"):
        super().__init__(
            message=message,
            error_code="RATE_LIMITED",
            status_code=429,
        )


class FetchTimeoutError(ForumScraperBaseError):
    """Raised when the request times out."""

    def __init__(self, message: str = "Request timed out"):
        super().__init__(
            message=message,
            error_code="FETCH_TIMEOUT",
            status_code=504,
        )


class ParseError(ForumScraperBaseError):
    """Raised when response data cannot be parsed."""

    def __init__(self, message: str = "Failed to parse response"):
        super().__init__(
            message=message,
            error_code="PARSE_ERROR",
            status_code=500,
        )


class MaxRetriesError(ForumScraperBaseError):
    """Raised when all retry attempts have been exhausted."""

    def __init__(self, message: str = "Failed after maximum retry attempts"):
        super().__init__(
            message=message,
            error_code="MAX_RETRIES_EXCEEDED",
            status_code=503,
        )
