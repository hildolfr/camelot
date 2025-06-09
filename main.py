"""
Camelot - Main FastAPI application
A web interface and REST API for the poker_knight module.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from src.camelot.api.calculator import router as api_router
from src.camelot.web.routes import router as web_router

# Create FastAPI app
app = FastAPI(
    title="Camelot",
    description="A web interface and REST API for Texas Hold'em poker calculations",
    version="0.0.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS for API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(api_router)
app.include_router(web_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🏰 Camelot is starting up...")
    print("🃏 Poker Knight module ready for calculations")
    print("📡 API docs available at /api/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    print("🏰 Camelot is shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    # Run with hot reload for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )