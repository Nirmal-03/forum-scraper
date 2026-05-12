"""Product Hunt Scraper — orchestrates the full scraping flow.

Implements BaseScraper interface: validate → fetch → extract → normalize.
Scrapes forum posts (threads) from a Product Hunt product community page.
"""

import random
import time

from interfaces.base_scraper import BaseScraper
from models.response import Post
from scrapers.producthunt.extractor import extract_forum_posts
from scrapers.producthunt.fetcher import fetch_forum_page
from scrapers.producthunt.models import validate_producthunt_url


class ProductHuntScraper(BaseScraper):
    """Scraper implementation for Product Hunt forum posts."""

    def validate(self, url: str, options: dict | None = None) -> bool:
        """Validate that the URL is a valid Product Hunt forum URL."""
        validate_producthunt_url(url)
        return True

    def scrape(self, url: str, limit: int, options: dict | None = None) -> dict:
        """Scrape posts from a Product Hunt product forum page.

        Args:
            url: Product Hunt URL (e.g., https://www.producthunt.com/p/zoho).
            limit: Maximum number of posts to fetch.
            options: Optional dict with 'sort' (trending, popular, featured, new).

        Returns:
            Dict with product_slug, total_fetched, and posts.
        """
        product_slug = validate_producthunt_url(url)

        sort = ""
        if options and isinstance(options.get("sort"), str):
            sort = options["sort"].lower()
            if sort not in ("trending", "popular", "featured", "new"):
                sort = ""

        all_posts: list[dict] = []
        page = 1

        while len(all_posts) < limit:
            html = fetch_forum_page(product_slug, page=page, sort=sort)
            posts, has_next, total_count = extract_forum_posts(html)

            if not posts:
                break

            all_posts.extend(posts)

            if not has_next:
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.0))

        # Hard limit slice
        all_posts = all_posts[:limit]

        # Normalize
        normalized = [self.normalize(p) for p in all_posts]

        return {
            "product_slug": product_slug,
            "total_fetched": len(normalized),
            "posts": [p.model_dump() for p in normalized],
        }

    def normalize(self, raw: dict) -> Post:
        """Convert raw PH post dict into unified Post model."""
        return Post(
            id=str(raw.get("id", "")),
            title=str(raw.get("title", "")),
            author=str(raw.get("author", "Unknown")),
            score=int(raw.get("score", 0)),
            upvote_ratio=0.0,
            num_comments=int(raw.get("comments_count", 0)),
            created_utc=0.0,
            url=str(raw.get("url", "")),
            permalink=str(raw.get("path", "")),
            selftext=str(raw.get("description", "")),
            link_flair_text=str(raw.get("tagline", "")),
            is_self=True,
            thumbnail=str(raw.get("author_avatar_url", "")),
        )
