"""Stack Overflow extraction logic.

Parses the SE API JSON response to extract questions.
"""

from core.exceptions import ParseError


def extract_questions(data: dict) -> tuple[list[dict], bool]:
    """Extract questions from a Stack Overflow API response.

    Args:
        data: Parsed JSON from the SE API.

    Returns:
        Tuple of (questions_list, has_more).

    Raises:
        ParseError: If response structure is unexpected.
    """
    try:
        if "items" not in data:
            if "error_message" in data:
                raise ParseError(f"SO API error: {data['error_message']}")
            raise ParseError("No 'items' field in Stack Overflow response")

        items = data["items"]
        has_more = data.get("has_more", False)

        questions = []
        for item in items:
            question = _extract_question(item)
            questions.append(question)

        return questions, has_more

    except ParseError:
        raise
    except Exception as e:
        raise ParseError(f"Failed to parse Stack Overflow response: {str(e)}")


def _extract_question(item: dict) -> dict:
    """Extract a single question from an API item.

    Args:
        item: A question object from the SE API.

    Returns:
        Dict with normalized question fields.
    """
    owner = item.get("owner", {})
    tags = item.get("tags", [])

    return {
        "id": str(item.get("question_id", "")),
        "title": item.get("title", ""),
        "author": owner.get("display_name", "Unknown"),
        "author_profile": owner.get("link", ""),
        "author_reputation": owner.get("reputation", 0),
        "score": int(item.get("score", 0)),
        "answer_count": int(item.get("answer_count", 0)),
        "view_count": int(item.get("view_count", 0)),
        "is_answered": bool(item.get("is_answered", False)),
        "creation_date": int(item.get("creation_date", 0)),
        "last_activity_date": int(item.get("last_activity_date", 0)),
        "link": item.get("link", ""),
        "body": item.get("body", ""),
        "tags": tags,
    }
