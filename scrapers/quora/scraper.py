"""Quora Scraper — orchestrates the full scraping flow.

Implements BaseScraper interface: validate → fetch → extract → normalize.
Scrapes questions from Quora topic pages via internal GraphQL API.
"""

import time
import random

from interfaces.base_scraper import BaseScraper
from models.response import Post
from scrapers.quora.extractor import extract_questions_from_feed
from scrapers.quora.fetcher import QuoraFetcher
from scrapers.quora.models import validate_quora_url


class QuoraScraper(BaseScraper):
    """Scraper implementation for Quora topic pages."""

    def validate(self, url: str, options: dict | None = None) -> bool:
        """Validate that the URL is a valid Quora topic URL."""
        validate_quora_url(url)
        return True

    def scrape(self, url: str, limit: int, options: dict | None = None) -> dict:
        """Scrape questions from a Quora topic page.

        Args:
            url: Quora topic URL.
            limit: Maximum number of questions to fetch.
            options: Optional dict (unused).

        Returns:
            Dict with topic_slug, total_fetched, and posts.
        """
        url_info = validate_quora_url(url)
        topic_slug = url_info["topic_slug"]
        normalized_url = url_info["url"]

        # Initialize fetcher (gets auth tokens and feed hash)
        fetcher = QuoraFetcher()
        fetcher.initialize(normalized_url)

        all_questions: list[dict] = []
        seen_qids: set[int] = set()
        cursor: str | None = None
        page_num = 0

        while len(all_questions) < limit:
            response_data = fetcher.fetch_feed_page(cursor=cursor, page_num=page_num)
            questions, next_cursor = extract_questions_from_feed(response_data)

            if not questions:
                break

            # Deduplicate across pages
            for q in questions:
                if q["qid"] not in seen_qids and len(all_questions) < limit:
                    seen_qids.add(q["qid"])
                    all_questions.append(q)

            if not next_cursor or len(all_questions) >= limit:
                break

            cursor = next_cursor
            page_num += 1
            time.sleep(random.uniform(1.0, 2.0))

        # Normalize
        normalized = [self.normalize(q) for q in all_questions]

        return {
            "topic": topic_slug,
            "total_fetched": len(normalized),
            "posts": [p.model_dump() for p in normalized],
        }

    def normalize(self, raw: dict) -> Post:
        """Convert raw Quora question dict into unified Post model."""
        return Post(
            id=str(raw.get("qid", "")),
            title=str(raw.get("title", "")),
            author="",
            score=0,
            upvote_ratio=0.0,
            num_comments=int(raw.get("answer_count", 0)),
            created_utc=float(raw.get("created_time", 0)),
            url=str(raw.get("url", "")),
            permalink=str(raw.get("url", "")),
            selftext="",
            link_flair_text="quora",
            is_self=True,
            thumbnail="",
        )
