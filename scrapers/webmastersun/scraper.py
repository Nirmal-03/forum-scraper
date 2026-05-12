"""WebmasterSun Scraper — orchestrates the full scraping flow.

Implements BaseScraper interface: validate → fetch → extract → normalize.
Scrapes search results from WebmasterSun XenForo forum.
"""

import random
import time

from interfaces.base_scraper import BaseScraper
from models.response import Post
from scrapers.webmastersun.extractor import extract_post_content, extract_search_posts
from scrapers.webmastersun.fetcher import fetch_post_page, fetch_search_page
from scrapers.webmastersun.models import validate_webmastersun_url


class WebmasterSunScraper(BaseScraper):
    """Scraper implementation for WebmasterSun search results."""

    def validate(self, url: str, options: dict | None = None) -> bool:
        """Validate that the URL is a valid WebmasterSun search URL."""
        validate_webmastersun_url(url)
        return True

    def scrape(self, url: str, limit: int, options: dict | None = None) -> dict:
        """Scrape posts from WebmasterSun search results.

        Args:
            url: WebmasterSun search URL.
            limit: Maximum number of posts to fetch.
            options: Optional dict (unused).

        Returns:
            Dict with query, total_fetched, and posts.
        """
        url_info = validate_webmastersun_url(url)
        base_url = url_info["base_url"]
        query = url_info["query"]

        all_posts: list[dict] = []
        page = 1

        while len(all_posts) < limit:
            html = fetch_search_page(base_url, page=page)
            posts, has_next = extract_search_posts(html)

            if not posts:
                break

            all_posts.extend(posts)

            if not has_next:
                break

            page += 1
            time.sleep(random.uniform(1.5, 3.0))

        # Hard limit slice
        all_posts = all_posts[:limit]

        # Fetch full content for each post
        for post in all_posts:
            post_url = post.get("url", "")
            post_id = post.get("id", "")
            if post_url and post_id:
                try:
                    page_html = fetch_post_page(post_url)
                    full_content = extract_post_content(page_html, post_id)
                    if full_content:
                        post["full_content"] = full_content
                except Exception:
                    # If fetching full content fails, keep the snippet
                    pass
                time.sleep(random.uniform(1.0, 2.0))

        # Normalize
        normalized = [self.normalize(p) for p in all_posts]

        return {
            "query": query,
            "search_id": url_info["search_id"],
            "total_fetched": len(normalized),
            "posts": [p.model_dump() for p in normalized],
        }

    def normalize(self, raw: dict) -> Post:
        """Convert raw WebmasterSun post dict into unified Post model."""
        # Prefer full_content over snippet
        content = raw.get("full_content") or raw.get("snippet", "")
        return Post(
            id=str(raw.get("id", "")),
            title=str(raw.get("title", "")),
            author=str(raw.get("author", "Unknown")),
            score=0,
            upvote_ratio=0.0,
            num_comments=int(raw.get("post_number", 0)),
            created_utc=float(raw.get("timestamp", 0)),
            url=str(raw.get("url", "")),
            permalink=str(raw.get("url", "")),
            selftext=content,
            link_flair_text=str(raw.get("forum", "")),
            is_self=True,
            thumbnail="",
        )
