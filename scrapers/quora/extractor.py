"""Quora extraction logic.

Parses the GraphQL feed response to extract question data.
"""

import json

from core.exceptions import ParseError


def extract_questions_from_feed(response_data: dict) -> tuple[list[dict], str | None]:
    """Extract questions from a Quora feed GraphQL response.

    Args:
        response_data: Raw JSON dict from the GraphQL API.

    Returns:
        Tuple of (questions_list, next_cursor).
        next_cursor is None if there are no more pages.

    Raises:
        ParseError: If the response structure is unexpected.
    """
    try:
        data = response_data.get("data", {})
        multifeed = data.get("multifeedObject", {})
        conn = multifeed.get("multifeedConnection", {})

        edges = conn.get("edges", [])
        page_info = conn.get("pageInfo", {})

        questions = []
        seen_qids = set()

        for edge in edges:
            node = edge.get("node", {})
            bundle_conn = node.get("bundleConnection", {})
            bundle_edges = bundle_conn.get("edges", [])

            for bundle_edge in bundle_edges:
                bundle_node = bundle_edge.get("node", {})
                answer = bundle_node.get("answer", {})
                if not answer:
                    continue

                question = answer.get("question", {})
                if not question:
                    continue

                qid = question.get("qid")
                if not qid or qid in seen_qids:
                    continue
                seen_qids.add(qid)

                title_raw = question.get("title", "")
                title = _parse_json_text(title_raw)
                url = question.get("url", "")
                slug = question.get("slug", "")
                answer_count = question.get("answerCount", 0)

                # Extract asker info
                asker = question.get("asker", {})
                asker_uid = asker.get("uid") if isinstance(asker, dict) else None

                # Get answer creation time as proxy for question activity
                created_time = answer.get("creationTime", 0)

                questions.append({
                    "qid": qid,
                    "title": title,
                    "url": f"https://www.quora.com{url}" if url.startswith("/") else url,
                    "slug": slug,
                    "answer_count": answer_count or 0,
                    "created_time": created_time or 0,
                })

        # Determine next cursor
        has_next = page_info.get("hasNextPage", False)
        next_cursor = page_info.get("endCursor") if has_next else None

        return questions, next_cursor

    except (KeyError, TypeError, AttributeError) as e:
        raise ParseError(f"Failed to parse Quora feed response: {e}")


def _parse_json_text(text_json: str) -> str:
    """Parse Quora's JSON-encoded text format into plain text.

    Quora stores titles/content as JSON with sections and spans:
    {"sections": [{"spans": [{"text": "...", "modifiers": {}}]}]}

    Args:
        text_json: JSON string or plain text.

    Returns:
        Plain text string.
    """
    if not text_json:
        return ""

    # If it doesn't look like JSON, return as-is
    if not text_json.startswith("{"):
        return text_json

    try:
        data = json.loads(text_json)
        parts = []
        for section in data.get("sections", []):
            for span in section.get("spans", []):
                parts.append(span.get("text", ""))
        return "".join(parts)
    except (json.JSONDecodeError, TypeError):
        return text_json
