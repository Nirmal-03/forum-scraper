"""Stack Overflow Scraper — orchestrates the full scraping flow.

Implements BaseScraper interface: validate → fetch → extract → normalize.
Scrapes questions by tag from Stack Overflow using the SE API v2.3.
"""

import time

from interfaces.base_scraper import BaseScraper
from models.response import Post
from scrapers.stackoverflow.extractor import extract_questions
from scrapers.stackoverflow.fetcher import fetch_questions
from scrapers.stackoverflow.models import validate_stackoverflow_url


VALID_SORTS = ("activity", "votes", "creation", "hot", "week", "month")


class StackOverflowScraper(BaseScraper):
    """Scraper implementation for Stack Overflow questions by tag."""

    def validate(self, url: str, options: dict | None = None) -> bool:
        """Validate that the URL is a valid SO tagged URL."""
        validate_stackoverflow_url(url)
        return True

    def scrape(self, url: str, limit: int, options: dict | None = None) -> dict:
        """Scrape questions from Stack Overflow by tag.

        Args:
            url: SO URL (e.g., https://stackoverflow.com/questions/tagged/zohobooks).
            limit: Maximum number of questions to fetch.
            options: Optional dict with 'sort' (activity, votes, creation, hot, week, month).

        Returns:
            Dict with tag, total_fetched, and posts.
        """
        tag = validate_stackoverflow_url(url)

        sort = "activity"
        if options and isinstance(options.get("sort"), str):
            sort = options["sort"].lower()
            if sort not in VALID_SORTS:
                sort = "activity"

        all_questions: list[dict] = []
        page = 1

        while len(all_questions) < limit:
            remaining = limit - len(all_questions)
            pagesize = min(remaining, 100)

            raw_data = fetch_questions(
                tag=tag,
                sort=sort,
                page=page,
                pagesize=pagesize,
            )

            questions, has_more = extract_questions(raw_data)

            if not questions:
                break

            all_questions.extend(questions)

            if not has_more:
                break

            page += 1
            time.sleep(0.5)  # Light delay — API key gives 10k req/day

        # Hard limit slice
        all_questions = all_questions[:limit]

        # Normalize
        normalized = [self.normalize(q) for q in all_questions]

        return {
            "tag": tag,
            "total_fetched": len(normalized),
            "posts": [p.model_dump() for p in normalized],
        }

    def normalize(self, raw: dict) -> Post:
        """Convert raw SO question dict into unified Post model."""
        return Post(
            id=raw.get("id", ""),
            title=raw.get("title", ""),
            author=raw.get("author", "Unknown"),
            score=int(raw.get("score", 0)),
            upvote_ratio=0.0,
            num_comments=int(raw.get("answer_count", 0)),
            created_utc=float(raw.get("creation_date", 0)),
            url=raw.get("link", ""),
            permalink=raw.get("link", ""),
            selftext=raw.get("body", ""),
            link_flair_text=", ".join(raw.get("tags", [])),
            is_self=True,
            thumbnail="",
        )
