"""Abstract base class (Interface) for all forum scrapers.

Every forum scraper MUST implement this interface to ensure
uniform behavior and enable the factory pattern.
"""

from abc import ABC, abstractmethod

from pydantic import BaseModel


class BaseScraper(ABC):
    """Interface that all forum scrapers must implement."""

    @abstractmethod
    def validate(self, url: str, **kwargs) -> bool:
        """Validate if the URL is valid for this forum.

        Args:
            url: The URL to validate.

        Returns:
            True if valid.

        Raises:
            InvalidURLError: If the URL is not valid for this forum.
        """
        ...

    @abstractmethod
    def scrape(self, url: str, limit: int, options: dict | None = None) -> dict:
        """Orchestrate the full scraping flow: validate → fetch → extract → normalize.

        Args:
            url: The forum URL to scrape.
            limit: Maximum number of items to return.
            options: Optional forum-specific parameters.

        Returns:
            Dict with forum-specific fields + total_fetched and data list.
        """
        ...

    @abstractmethod
    def normalize(self, raw: dict) -> BaseModel:
        """Convert a raw forum-specific item into a normalized model.

        Args:
            raw: Raw data from the forum.

        Returns:
            A normalized Post instance.
        """
        ...
