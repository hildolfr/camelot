"""
Initialize the caching system for Camelot.
"""

import os
from .cache_storage import CacheStorage
from .cached_poker_calculator import CachedPokerCalculator
from .cache_manager import CacheManager


# Global cache storage instance
_cache_storage = None
_cached_calculator = None


def get_cache_storage() -> CacheStorage:
    """Get or create the global cache storage instance."""
    global _cache_storage
    if _cache_storage is None:
        # Get configuration from environment or use defaults
        memory_limit_mb = int(os.getenv("CAMELOT_CACHE_MEMORY_MB", 2048))
        db_path = os.getenv("CAMELOT_CACHE_PATH", "~/.camelot_cache/camelot_cache.db")
        
        _cache_storage = CacheStorage(
            memory_limit_mb=memory_limit_mb,
            db_path=db_path
        )
    
    return _cache_storage


def get_cached_calculator() -> CachedPokerCalculator:
    """Get or create the global cached calculator instance."""
    global _cached_calculator
    if _cached_calculator is None:
        cache_storage = get_cache_storage()
        _cached_calculator = CachedPokerCalculator(cache_storage)
    
    return _cached_calculator


def get_cache_manager() -> CacheManager:
    """Get a cache manager instance."""
    calculator = get_cached_calculator()
    return CacheManager(calculator)


def initialize_cache_system():
    """Initialize the entire cache system."""
    print("🔧 Initializing Camelot cache system...")
    
    # Get instances to ensure they're created
    cache_storage = get_cache_storage()
    calculator = get_cached_calculator()
    
    # Print initial stats
    stats = cache_storage.get_stats()
    print(f"📊 Cache initialized:")
    print(f"   - Memory limit: {stats['memory_limit_mb']:.0f} MB")
    print(f"   - SQLite entries: {stats['sqlite_entries']:,}")
    print(f"   - Database size: {stats['sqlite_size_mb']:.1f} MB")
    
    return calculator, cache_storage