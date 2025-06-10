"""
Camelot - Main FastAPI application
A web interface and REST API for the poker_knight module.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import asyncio
import logging

from src.camelot.api.calculator import router as api_router
from src.camelot.api import calculator as calc_module
from src.camelot.api.game_routes import router as game_router
from src.camelot.web.routes import router as web_router
from src.camelot.core.cache_init import initialize_cache_system, get_cache_manager
import config

# Configure logging
logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
logger = logging.getLogger(__name__)

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
app.include_router(game_router)
app.include_router(web_router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🏰 Camelot is starting up...")
    
    # Initialize cache system
    calculator, cache_storage = initialize_cache_system()
    
    if config.ENABLE_CACHE:
        # Initialize cache manager for warming
        cache_manager = get_cache_manager()
        calc_module.cache_manager = cache_manager  # Set reference for API endpoint
        
        # Start cache warming in background - don't await!
        asyncio.create_task(initialize_cache_background(cache_manager))
        print("📊 Cache warming started in background")
    else:
        print("💾 Cache warming disabled")
    
    print("🃏 Poker Knight module ready for calculations")
    print("📡 API docs available at /api/docs")


async def initialize_cache_background(cache_manager):
    """Initialize cache in the background without blocking startup."""
    try:
        cache_stats = await cache_manager.initialize_cache(full_preload=config.FULL_PRELOAD)
        logger.info(f"📊 Cache initialized: {cache_stats.get('scenarios_cached', 0)} scenarios cached in {cache_stats['startup_time']:.1f}s")
        if cache_stats['background_tasks'] > 0:
            logger.info(f"🔄 Background caching in progress ({cache_stats['background_tasks']} tasks)...")
    except Exception as e:
        logger.error(f"❌ Cache initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    print("🏰 Camelot is shutting down...")


if __name__ == "__main__":
    import uvicorn
    
    # Run with hot reload for development
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.RELOAD,
        log_level=config.LOG_LEVEL.lower(),
        # Exclude cache files from file watcher
        reload_excludes=["*.db", "*.db-journal", "*_cache*", "*.log"]
    )