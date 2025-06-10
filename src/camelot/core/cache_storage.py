"""
Cache storage implementation for Camelot.
Provides a hybrid memory/SQLite caching system for poker calculations.
"""

import os
import sqlite3
import json
import time
import threading
from typing import Dict, Optional, Any
from collections import OrderedDict
from contextlib import contextmanager


class CacheStorage:
    """Hybrid memory/SQLite cache storage for poker calculations."""
    
    def __init__(self, memory_limit_mb: int = 2048, db_path: str = "~/.camelot_cache/camelot_cache.db"):
        """
        Initialize cache storage.
        
        Args:
            memory_limit_mb: Maximum memory cache size in MB (default 2GB)
            db_path: Path to SQLite database file
        """
        self.memory_limit = memory_limit_mb * 1024 * 1024  # Convert to bytes
        self.db_path = os.path.expanduser(db_path)
        
        # Create cache directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize memory cache as OrderedDict for LRU
        self.memory_cache = OrderedDict()
        self.memory_size = 0
        self.cache_lock = threading.RLock()
        
        # Initialize SQLite database
        self._init_database()
        
        # Statistics
        self.stats = {
            'memory_hits': 0,
            'sqlite_hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create main cache table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cache_key TEXT UNIQUE NOT NULL,
                    hero_hand TEXT NOT NULL,
                    num_opponents INTEGER NOT NULL,
                    board_cards TEXT,
                    simulation_mode TEXT NOT NULL,
                    result_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 1
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_entries(cache_key)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hero_hand ON cache_entries(hero_hand)")
            
            # Create metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Set database pragmas for performance
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=10000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            
            conn.commit()
    
    @contextmanager
    def _get_db_connection(self):
        """Get a database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            yield conn
        finally:
            conn.close()
    
    def _estimate_memory_size(self, key: str, value: Dict) -> int:
        """Estimate memory size of a cache entry."""
        # Rough estimation: key size + JSON size + overhead
        return len(key) + len(json.dumps(value)) + 64
    
    def get(self, key: str) -> Optional[Dict]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached result dictionary or None if not found
        """
        with self.cache_lock:
            # Check memory cache first
            if key in self.memory_cache:
                # Move to end (LRU)
                self.memory_cache.move_to_end(key)
                self.stats['memory_hits'] += 1
                return self.memory_cache[key].copy()
            
            # Check SQLite cache
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE cache_entries 
                        SET last_accessed = CURRENT_TIMESTAMP,
                            access_count = access_count + 1
                        WHERE cache_key = ?
                        RETURNING result_json
                    """, (key,))
                    
                    row = cursor.fetchone()
                    if row:
                        result = json.loads(row[0])
                        
                        # Add to memory cache
                        self._add_to_memory_cache(key, result)
                        
                        self.stats['sqlite_hits'] += 1
                        conn.commit()
                        return result
                    
            except Exception as e:
                print(f"Error retrieving from SQLite cache: {e}")
            
            self.stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Dict, hero_hand: str = "", num_opponents: int = 0, 
            board_cards: str = "", simulation_mode: str = "default"):
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Result dictionary to cache
            hero_hand: Hero's hand for metadata
            num_opponents: Number of opponents for metadata
            board_cards: Board cards for metadata
            simulation_mode: Simulation mode for metadata
        """
        with self.cache_lock:
            # Add to memory cache
            self._add_to_memory_cache(key, value)
            
            # Add to SQLite cache
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (cache_key, hero_hand, num_opponents, board_cards, 
                         simulation_mode, result_json, created_at, last_accessed, access_count)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                                COALESCE((SELECT access_count FROM cache_entries WHERE cache_key = ?), 0) + 1)
                    """, (key, hero_hand, num_opponents, board_cards, 
                          simulation_mode, json.dumps(value), key))
                    conn.commit()
            except Exception as e:
                print(f"Error storing in SQLite cache: {e}")
    
    def _add_to_memory_cache(self, key: str, value: Dict):
        """Add entry to memory cache with LRU eviction."""
        entry_size = self._estimate_memory_size(key, value)
        
        # Remove existing entry if present
        if key in self.memory_cache:
            old_size = self._estimate_memory_size(key, self.memory_cache[key])
            self.memory_size -= old_size
            del self.memory_cache[key]
        
        # Evict entries if needed
        while self.memory_size + entry_size > self.memory_limit and self.memory_cache:
            # Remove least recently used
            oldest_key, oldest_value = self.memory_cache.popitem(last=False)
            self.memory_size -= self._estimate_memory_size(oldest_key, oldest_value)
            self.stats['evictions'] += 1
        
        # Add new entry
        self.memory_cache[key] = value.copy()
        self.memory_size += entry_size
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.cache_lock:
            total_hits = self.stats['memory_hits'] + self.stats['sqlite_hits']
            total_requests = total_hits + self.stats['misses']
            
            stats = self.stats.copy()
            stats.update({
                'memory_entries': len(self.memory_cache),
                'memory_size_mb': self.memory_size / (1024 * 1024),
                'memory_limit_mb': self.memory_limit / (1024 * 1024),
                'hit_rate': (total_hits / total_requests * 100) if total_requests > 0 else 0
            })
            
            # Get SQLite stats
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM cache_entries")
                    stats['sqlite_entries'] = cursor.fetchone()[0]
                    
                    # Get database file size
                    stats['sqlite_size_mb'] = os.path.getsize(self.db_path) / (1024 * 1024)
            except:
                stats['sqlite_entries'] = 0
                stats['sqlite_size_mb'] = 0
            
            return stats
    
    def clear_memory_cache(self):
        """Clear memory cache only."""
        with self.cache_lock:
            self.memory_cache.clear()
            self.memory_size = 0
    
    def clear_all(self):
        """Clear both memory and SQLite cache."""
        with self.cache_lock:
            self.clear_memory_cache()
            
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM cache_entries")
                    cursor.execute("DELETE FROM cache_metadata")
                    conn.commit()
            except Exception as e:
                print(f"Error clearing SQLite cache: {e}")
            
            # Reset statistics
            self.stats = {
                'memory_hits': 0,
                'sqlite_hits': 0,
                'misses': 0,
                'evictions': 0
            }