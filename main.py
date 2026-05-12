"""Forum Review Scraper — FastAPI application entry point.

A backend API that scrapes posts/threads from multiple forum platforms
through a single endpoint. The platform is dynamically chosen based on input.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.v1.routes.scraper import router as scraper_router
from core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Scrape posts/threads from multiple forum platforms through a single API endpoint.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware — allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(scraper_router, prefix="/api/v1", tags=["Scraper"])


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/ui", response_class=HTMLResponse, tags=["UI"])
def serve_ui():
    """Serve the browser-based scraper UI."""
    ui_path = Path(__file__).parent / "ui" / "index.html"
    return HTMLResponse(content=ui_path.read_text(), status_code=200)
