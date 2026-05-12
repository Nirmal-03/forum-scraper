"""Reddit extraction logic.

Parses Reddit's JSON structure to extract posts (t3) from subreddit listings.
"""

from core.exceptions import ParseError


def extract_subreddit_posts(data: dict) -> tuple[list[dict], str | None]:
    """Extract posts from a subreddit listing response.

    Args:
        data: The parsed JSON response from a subreddit listing.

    Returns:
        Tuple of (posts_list, after_cursor). after_cursor is None when no more pages.

    Raises:
        ParseError: If the response structure is unexpected.
    """
    try:
        if not isinstance(data, dict):
            raise ParseError("Unexpected subreddit response structure")

        listing_data = data.get("data", {})
        after = listing_data.get("after")  # Pagination cursor
        children = listing_data.get("children", [])

        posts = []
        for child in children:
            if child.get("kind") == "t3":
                post_data = child["data"]
                posts.append({
                    "id": post_data.get("id", ""),
                    "title": post_data.get("title", ""),
                    "author": post_data.get("author", "[deleted]"),
                    "score": post_data.get("score", 0),
                    "upvote_ratio": post_data.get("upvote_ratio", 0.0),
                    "num_comments": post_data.get("num_comments", 0),
                    "created_utc": post_data.get("created_utc", 0),
                    "url": post_data.get("url", ""),
                    "permalink": f"https://www.reddit.com{post_data.get('permalink', '')}",
                    "selftext": post_data.get("selftext", ""),
                    "link_flair_text": post_data.get("link_flair_text", ""),
                    "is_self": post_data.get("is_self", False),
                    "thumbnail": post_data.get("thumbnail", ""),
                })

        return posts, after

    except (KeyError, IndexError, TypeError) as e:
        raise ParseError(f"Failed to parse subreddit response: {e}")
