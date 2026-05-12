"""Single scrape endpoint — POST /api/v1/scrape.

This route handles all forum scraping requests through a unified interface.
The correct scraper is dynamically selected based on the 'forum' field.
"""

from fastapi import APIRouter, HTTPException

from core.exceptions import ForumScraperBaseError
from core.response import ErrorResponse, SuccessResponse
from factory.scraper_factory import ScraperFactory
from models.request import ScrapeRequest

router = APIRouter()


@router.post(
    "/scrape",
    response_model=SuccessResponse,
    responses={
        400: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
def scrape_forum(request: ScrapeRequest):
    """Scrape posts from a subreddit/forum.

    Dynamically routes to the correct scraper based on the 'forum' field.

    - **forum**: Target forum (e.g., "reddit")
    - **url**: Subreddit URL to scrape (e.g., https://www.reddit.com/r/Zoho/)
    - **limit**: Maximum number of posts (default: 100)
    - **options**: Optional forum-specific parameters
    """
    try:
        # Factory resolves the correct scraper
        scraper = ScraperFactory.get_scraper(request.forum)

        # Execute the scraping pipeline
        result = scraper.scrape(
            url=request.url,
            limit=request.limit,
            options=request.options,
        )

        return SuccessResponse(
            forum=request.forum,
            total_fetched=result.pop("total_fetched"),
            **result,
        )

    except ForumScraperBaseError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=ErrorResponse(
                forum=request.forum,
                error_code=e.error_code,
                message=e.message,
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                forum=request.forum,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
            ).model_dump(),
        )
