"""Web UI routes."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

# Set up templates directory
templates_dir = Path(__file__).parent.parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter(tags=["web"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main calculator page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Camelot Poker Calculator"}
    )


@router.get("/game", response_class=HTMLResponse)
async def poker_game(request: Request):
    """Render the poker game page."""
    return templates.TemplateResponse(
        "poker_game.html",
        {"request": request, "title": "Camelot Poker Game"}
    )


@router.get("/system", response_class=HTMLResponse)
async def system_testing(request: Request):
    """Render the system and testing utilities page."""
    return templates.TemplateResponse(
        "system_testing.html",
        {"request": request, "title": "System & Testing - Camelot"}
    )


@router.get("/logs", response_class=HTMLResponse)
async def log_viewer(request: Request):
    """Render the log viewer page."""
    return templates.TemplateResponse(
        "log_viewer.html",
        {"request": request, "title": "Log Viewer - Camelot"}
    )