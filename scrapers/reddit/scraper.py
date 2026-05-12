"""Reddit Scraper — orchestrates the full scraping flow.

Implements BaseScraper interface: validate → fetch → extract → normalize.
Scrapes all posts from a subreddit (paginated).
No caching — always fetches fresh data from Reddit.
"""

import random
import time

from interfaces.base_scraper import BaseScraper
from models.response import Post
from scrapers.reddit.extractor import extract_subreddit_posts
from scrapers.reddit.fetcher import fetch_subreddit_posts
from scrapers.reddit.models import validate_subreddit_url


class RedditScraper(BaseScraper):
    """Scraper implementation for Reddit subreddits."""

    def validate(self, url: str, **kwargs) -> bool:
        """Validate that the URL is a valid subreddit URL."""
        validate_subreddit_url(url)
        return True

    def scrape(self, url: str, limit: int, options: dict | None = None) -> dict:
        """Scrape posts from a subreddit with pagination.

        Args:
            url: Subreddit URL (e.g., https://www.reddit.com/r/Zoho/).
            limit: Maximum number of posts to fetch.
            options: Optional dict with 'sort' key (hot, new, top, rising).

        Returns:
            Dict with subreddit, total_fetched, and posts.
        """
        subreddit = validate_subreddit_url(url)

        sort = "hot"
        if options and isinstance(options.get("sort"), str):
            sort = options["sort"]

        all_posts = []
        after = None

        while len(all_posts) < limit:
            # Fetch one page (max 100 per Reddit API)
            remaining = limit - len(all_posts)
            page_limit = min(remaining, 100)

            raw_data = fetch_subreddit_posts(
                subreddit=subreddit,
                sort=sort,
                after=after,
                limit=page_limit,
            )

            posts, after = extract_subreddit_posts(raw_data)

            if not posts:
                break  # No more posts available

            all_posts.extend(posts)

            # Stop if no next page
            if not after:
                break

            # Human-like delay between pages
            time.sleep(random.uniform(1.5, 3.5))

        # Hard limit slice
        all_posts = all_posts[:limit]

        # Normalize
        normalized = [self.normalize(p) for p in all_posts]

        return {
            "subreddit": subreddit,
            "total_fetched": len(normalized),
            "posts": [p.model_dump() for p in normalized],
        }

    def normalize(self, raw: dict) -> Post:
        """Convert raw Reddit post dict into unified Post model."""
        return Post(
            id=str(raw.get("id", "")),
            title=str(raw.get("title", "")),
            author=str(raw.get("author", "[deleted]")),
            score=int(raw.get("score", 0)),
            upvote_ratio=float(raw.get("upvote_ratio", 0.0)),
            num_comments=int(raw.get("num_comments", 0)),
            created_utc=float(raw.get("created_utc", 0)),
            url=str(raw.get("url", "")),
            permalink=str(raw.get("permalink", "")),
            selftext=str(raw.get("selftext", "")),
            link_flair_text=str(raw.get("link_flair_text", "") or ""),
            is_self=bool(raw.get("is_self", False)),
            thumbnail=str(raw.get("thumbnail", "")),
        )
