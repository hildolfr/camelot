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
import time

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
        
        # Start periodic cache statistics logging
        asyncio.create_task(periodic_cache_stats(cache_storage))
        print("📈 Periodic cache statistics logging enabled (every 15s)")
    else:
        print("💾 Cache warming disabled")
    
    print("🃏 Poker Knight module ready for calculations")
    print("📡 API docs available at /api/docs")


async def periodic_cache_stats(cache_storage):
    """Log cache statistics every 15 seconds."""
    last_total_requests = 0
    last_time = time.time()
    
    # Base scenarios: 1326 hands * 6 opponents = 7956
    # But we can have 3 simulation modes, so theoretical max is 7956 * 3 = 23868
    base_scenarios = 7956  # 1326 unique starting hands * 6 opponent counts
    
    while True:
        try:
            await asyncio.sleep(15)  # Wait 15 seconds
            
            # Get cache statistics
            stats = cache_storage.get_stats()
            sqlite_entries = stats.get('sqlite_entries', 0)
            
            # Stop logging if we've reached or exceeded the base scenarios
            if sqlite_entries >= base_scenarios:
                logger.info(f"Cache fully populated with {sqlite_entries:,} entries. Stopping periodic updates.")
                break
            
            # Calculate fill rate based on base scenarios
            fill_rate = (sqlite_entries / base_scenarios * 100) if base_scenarios > 0 else 0
            
            # Calculate solution rate
            current_time = time.time()
            time_diff = current_time - last_time
            total_requests = stats.get('memory_hits', 0) + stats.get('sqlite_hits', 0) + stats.get('misses', 0)
            requests_diff = total_requests - last_total_requests
            
            # Calculate solutions per minute
            solutions_per_minute = (requests_diff / time_diff * 60) if time_diff > 0 else 0
            
            # Update for next iteration
            last_total_requests = total_requests
            last_time = current_time
            
            # Format the output
            print(f"\n📊 Cache Status Update:")
            print(f"├─ SQLite entries: {sqlite_entries:,} / {base_scenarios:,} ({fill_rate:.1f}% fill rate)")
            print(f"├─ Memory entries: {stats.get('memory_entries', 0):,} (limit: {stats.get('memory_limit_mb', 0):.0f}MB)")
            print(f"├─ Hit rate: {stats.get('hit_rate', 0):.1f}%")
            print(f"├─ Solution rate: {solutions_per_minute:.1f} solutions/min")
            print(f"├─ Cache hits: {stats.get('memory_hits', 0) + stats.get('sqlite_hits', 0):,} (Memory: {stats.get('memory_hits', 0):,}, SQLite: {stats.get('sqlite_hits', 0):,})")
            print(f"├─ Cache misses: {stats.get('misses', 0):,}")
            print(f"└─ DB size: {stats.get('sqlite_size_mb', 0):.1f}MB\n")
            
        except Exception as e:
            logger.error(f"Error logging cache stats: {e}")


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
        reload_excludes=[
            "*.db", 
            "*.db-journal", 
            "*_cache*", 
            "*.log",
            "logs/*",  # Exclude entire logs directory
            "*.pyc",   # Compiled Python files
            "__pycache__/*",  # Python cache directories
            "static/*",  # Static files don't need server reload
            "*.md",  # Documentation changes don't need reload
            "*.txt",  # Text files
            "venv/*",  # Virtual environment
            ".git/*",  # Git directory
        ]
    )