"""Scraper Factory — decides which scraper to use based on forum input.

Uses a registry pattern so adding new forums requires only
registering the new scraper class here.
"""

from core.exceptions import UnsupportedForumError
from interfaces.base_scraper import BaseScraper
from scrapers.producthunt.scraper import ProductHuntScraper
from scrapers.quora.scraper import QuoraScraper
from scrapers.reddit.scraper import RedditScraper
from scrapers.stackoverflow.scraper import StackOverflowScraper
from scrapers.webmastersun.scraper import WebmasterSunScraper

# Registry of supported forums → scraper classes
REGISTRY: dict[str, type[BaseScraper]] = {
    "reddit": RedditScraper,
    "producthunt": ProductHuntScraper,
    "stackoverflow": StackOverflowScraper,
    "webmastersun": WebmasterSunScraper,
    "quora": QuoraScraper,
}


class ScraperFactory:
    """Factory that returns the correct scraper instance based on forum name."""

    @staticmethod
    def get_scraper(forum: str) -> BaseScraper:
        """Get the appropriate scraper instance for the given forum.

        Args:
            forum: The forum identifier (e.g., "reddit").

        Returns:
            An instance of the appropriate scraper.

        Raises:
            UnsupportedForumError: If the forum is not in the registry.
        """
        forum_lower = forum.lower().strip()
        if forum_lower not in REGISTRY:
            raise UnsupportedForumError(forum_lower)
        return REGISTRY[forum_lower]()
