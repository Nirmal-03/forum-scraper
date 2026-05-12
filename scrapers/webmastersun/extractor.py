"""WebmasterSun extraction logic.

Parses the XenForo search results HTML to extract post data.
"""

import re

from core.exceptions import ParseError


def extract_search_posts(html: str) -> tuple[list[dict], bool]:
    """Extract posts from a WebmasterSun search results page.

    Args:
        html: Full HTML string of the search results page.

    Returns:
        Tuple of (posts_list, has_next_page).

    Raises:
        ParseError: If the HTML structure is unexpected.
    """
    try:
        posts = []

        # Split by block-row markers — each section is one search result
        marker = 'class="block-row block-row--separated'
        parts = html.split(marker)

        # Skip first part (before first result)
        for block_html in parts[1:]:
            # Extract author from data-author attribute
            author_match = re.search(r'data-author="([^"]*)"', block_html)
            author = author_match.group(1) if author_match else "Unknown"

            post = _extract_post_from_block(block_html, author)
            if post:
                posts.append(post)

        # Check if there's a next page
        has_next = 'rel="next"' in html or ">Next" in html

        return posts, has_next

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse WebmasterSun HTML: {str(e)}")


def _extract_post_from_block(block_html: str, author: str) -> dict | None:
    """Extract a single post from a search result block.

    Args:
        block_html: HTML of the block-row content.
        author: Author name from data-author attribute.

    Returns:
        Dict with post fields, or None if extraction fails.
    """
    # Extract title and URL
    title_match = re.search(
        r'<h3\s+class="contentRow-title">\s*<a\s+href="([^"]+)">(.*?)</a>',
        block_html,
        re.DOTALL,
    )
    if not title_match:
        return None

    path = title_match.group(1)
    raw_title = title_match.group(2)
    # Clean HTML from title (remove <em> highlights etc.)
    title = re.sub(r"<[^>]+>", "", raw_title).strip()
    title = _decode_html_entities(title)

    # Extract snippet
    snippet_match = re.search(
        r'<div\s+class="contentRow-snippet">(.*?)</div>',
        block_html,
        re.DOTALL,
    )
    snippet = ""
    if snippet_match:
        snippet = re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip()
        snippet = _decode_html_entities(snippet)

    # Extract metadata from listInline items
    # Post number
    post_num_match = re.search(r"Post #(\d+)", block_html)
    post_number = int(post_num_match.group(1)) if post_num_match else 0

    # Date (from datetime attribute)
    date_match = re.search(r'datetime="([^"]+)"', block_html)
    created_at = date_match.group(1) if date_match else ""

    # Unix timestamp
    timestamp_match = re.search(r'data-time="(\d+)"', block_html)
    timestamp = int(timestamp_match.group(1)) if timestamp_match else 0

    # Forum category
    forum_match = re.search(
        r'Forum:\s*<a\s+href="[^"]*">([^<]+)</a>',
        block_html,
    )
    forum_name = forum_match.group(1).strip() if forum_match else ""

    # Thread ID from URL
    thread_match = re.search(r"/threads/(\d+)-", path)
    thread_id = thread_match.group(1) if thread_match else ""

    # Post ID from URL
    post_id_match = re.search(r"post-(\d+)", path)
    post_id = post_id_match.group(1) if post_id_match else thread_id

    url = f"https://www.webmastersun.com{path}" if path.startswith("/") else path

    return {
        "id": post_id,
        "title": title,
        "snippet": snippet,
        "author": author,
        "post_number": post_number,
        "created_at": created_at,
        "timestamp": timestamp,
        "forum": forum_name,
        "thread_id": thread_id,
        "url": url,
    }


def extract_post_content(html: str, post_id: str) -> str:
    """Extract the full content of a specific post from a thread page.

    Args:
        html: Full HTML of the thread page.
        post_id: The post ID (numeric, e.g. "184519").

    Returns:
        Full text content of the post, or empty string if not found.
    """
    target = f'data-content="post-{post_id}"'
    post_start = html.find(target)
    if post_start == -1:
        return ""

    # Find the boundary of this post (next post or end)
    next_post = html.find('data-content="post-', post_start + len(target))
    if next_post == -1:
        post_section = html[post_start:]
    else:
        post_section = html[post_start:next_post]

    # Find bbWrapper content
    bb_marker = 'class="bbWrapper">'
    bb_start = post_section.find(bb_marker)
    if bb_start == -1:
        return ""

    content_start = bb_start + len(bb_marker)
    content_end = post_section.find("</div>", content_start)
    if content_end == -1:
        return ""

    raw_content = post_section[content_start:content_end]

    # Clean: replace <br> with newlines, strip tags, decode entities
    text = raw_content.replace("<br />", "\n").replace("<br>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = _decode_html_entities(text)
    return text.strip()

def _decode_html_entities(text: str) -> str:
    """Decode common HTML entities."""
    import html
    return html.unescape(text)
