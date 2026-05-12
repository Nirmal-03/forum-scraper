"""Product Hunt extraction logic.

Parses the embedded Apollo SSR data from the HTML page to extract
discussion threads (posts) from a Product Hunt product forum.
"""

import json

from core.exceptions import ParseError


def extract_forum_posts(html: str) -> tuple[list[dict], bool, int | None]:
    """Extract forum posts (threads) from a PH page HTML.

    Parses the Apollo SSR data embedded in the HTML to find the
    discussionForum threads listing.

    Args:
        html: Full HTML string of the PH forum page.

    Returns:
        Tuple of (posts_list, has_next_page, total_count).

    Raises:
        ParseError: If the response structure is unexpected or data not found.
    """
    try:
        # Find the discussionForum threads data block in HTML
        marker = '"threads":{"__typename":"DiscussionForumAssociationTypeConnectionWithCount"'
        idx = html.find(marker)
        if idx == -1:
            # Might be a 404 page or no threads
            if "not found" in html.lower()[:2000] or "404" in html[:500]:
                raise ParseError("Product Hunt forum not found")
            return [], False, 0

        # Find the enclosing {"data":...} object
        data_start = html.rfind('{"data":', max(0, idx - 300), idx)
        if data_start == -1:
            raise ParseError("Could not find data wrapper for threads")

        # Parse the JSON object by tracking braces
        chunk = html[data_start:data_start + 100000]
        depth = 0
        end_pos = 0
        for i, c in enumerate(chunk):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end_pos = i + 1
                    break

        if end_pos == 0:
            raise ParseError("Could not find end of threads data block")

        data = json.loads(chunk[:end_pos])
        forum = data.get("data", {}).get("discussionForum", {})
        threads_conn = forum.get("threads", {})
        edges = threads_conn.get("edges", [])
        page_info = threads_conn.get("pageInfo", {})
        total_count = threads_conn.get("totalCount")
        has_next = page_info.get("hasNextPage", False)

        # Extract posts from edges
        posts = []
        for edge in edges:
            node = edge.get("node", {})
            if not node:
                continue
            post = _extract_post(node, forum)
            posts.append(post)

        return posts, has_next, total_count

    except ParseError:
        raise
    except json.JSONDecodeError as e:
        raise ParseError(f"Failed to parse Product Hunt JSON data: {str(e)}")
    except Exception as e:
        raise ParseError(f"Failed to parse Product Hunt response: {str(e)}")


def _extract_post(node: dict, forum: dict) -> dict:
    """Extract a single post from a thread node.

    Args:
        node: The DiscussionForumAssociationType node.
        forum: The parent forum dict for context.

    Returns:
        Dict with normalized post fields.
    """
    commentable = node.get("commentable", {}) or {}
    user = node.get("user", {}) or {}
    subject = forum.get("subject", {}) or {}

    return {
        "id": str(node.get("id", "")),
        "title": node.get("title", ""),
        "slug": node.get("slug", ""),
        "path": node.get("path", ""),
        "description": node.get("descriptionPreview") or "",
        "author": user.get("name", "Unknown"),
        "author_username": user.get("username", ""),
        "author_avatar_url": user.get("avatarUrl", ""),
        "created_at": node.get("createdAt", ""),
        "comments_count": int(node.get("commentsCount", 0)),
        "score": int(commentable.get("latestScore", 0)),
        "tagline": commentable.get("tagline", ""),
        "is_featured": bool(node.get("isFeatured", False)),
        "is_pinned": bool(node.get("isPinned", False)),
        "product_name": subject.get("name", ""),
        "product_slug": subject.get("slug", ""),
        "url": f"https://www.producthunt.com{node.get('path', '')}",
    }
