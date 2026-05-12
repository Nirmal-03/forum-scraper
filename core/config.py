"""Global configuration and environment variables."""

import os


class Settings:
    """Application-wide settings loaded from environment."""

    APP_NAME: str = "Forum Review Scraper"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Reddit-specific
    REDDIT_BASE_URL: str = "https://www.reddit.com"
    REDDIT_REQUEST_TIMEOUT: int = 10
    REDDIT_MAX_RETRIES: int = 3
    REDDIT_CHUNK_SIZE: int = 100
    REDDIT_INITIAL_FETCH_LIMIT: int = 500

    # Product Hunt-specific
    PH_REQUEST_TIMEOUT: int = 15
    PH_MAX_RETRIES: int = 3

    # Stack Overflow-specific
    SO_API_KEY: str = os.getenv("SO_API_KEY", "")
    SO_BASE_URL: str = "https://api.stackexchange.com/2.3"
    SO_REQUEST_TIMEOUT: int = 10
    SO_MAX_RETRIES: int = 3
    SO_PAGE_SIZE: int = 100

    # WebmasterSun-specific
    WMS_REQUEST_TIMEOUT: int = 15
    WMS_MAX_RETRIES: int = 3

    # Quora-specific
    QUORA_REQUEST_TIMEOUT: int = 20
    QUORA_MAX_RETRIES: int = 3

    # Default limit
    DEFAULT_COMMENT_LIMIT: int = 100


settings = Settings()
