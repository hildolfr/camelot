"""
Cache manager for preloading poker calculations at startup.
Leverages poker_knight's built-in caching capabilities.
"""

import asyncio
import time
import os
from typing import List, Optional
from itertools import combinations
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages cache preloading and warming for poker calculations."""
    
    VALID_RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    VALID_SUITS = ['♠', '♥', '♦', '♣']
    
    # Priority hands for initial caching
    PRIORITY_HANDS = [
        # Premium hands
        ['A♠', 'A♥'], ['K♠', 'K♥'], ['Q♠', 'Q♥'], ['J♠', 'J♥'], ['10♠', '10♥'],
        ['A♠', 'K♠'], ['A♠', 'K♥'], ['A♠', 'Q♠'], ['A♠', 'J♠'],
        
        # Medium strength hands
        ['9♠', '9♥'], ['8♠', '8♥'], ['7♠', '7♥'], 
        ['A♠', '10♠'], ['K♠', 'Q♠'], ['K♠', 'J♠'], ['Q♠', 'J♠'],
        
        # Suited connectors
        ['J♠', '10♠'], ['10♠', '9♠'], ['9♠', '8♠'], ['8♠', '7♠'], ['7♠', '6♠'],
        
        # Common bluffs
        ['A♠', '5♠'], ['A♠', '4♠'], ['A♠', '3♠'], ['A♠', '2♠']
    ]
    
    def __init__(self, calculator):
        """Initialize cache manager with a poker calculator instance."""
        self.calculator = calculator
        self.cache_stats = {
            'preflop_cached': 0,
            'board_cached': 0,
            'total_time': 0,
            'errors': 0,
            'start_time': None,
            'elapsed_time': 0,
            'initial_cached': 0,  # Track what was already cached
            'new_cached': 0,      # Track new additions this session
            'total_expected': 0   # Total scenarios to cache
        }
        self._is_warming = False
        self._active_tasks = 0
        
        # Create a separate thread pool for cache warming with lower priority
        # Use only 2 threads to avoid overwhelming the system
        self._cache_executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="cache_warmer"
        )
    
    def generate_all_hands(self) -> List[List[str]]:
        """Generate all possible 2-card hands (1326 combinations)."""
        cards = []
        for rank in self.VALID_RANKS:
            for suit in self.VALID_SUITS:
                cards.append(f"{rank}{suit}")
        
        # Generate all 2-card combinations
        return [list(combo) for combo in combinations(cards, 2)]
    
    async def preload_priority_hands(self) -> None:
        """Preload high-priority hands for quick startup."""
        logger.info("🎯 Preloading priority hands...")
        self._active_tasks += 1
        start_time = time.time()
        
        # Create tasks for parallel execution
        tasks = []
        for hand in self.PRIORITY_HANDS:
            for opponents in range(1, 7):  # 1-6 opponents
                task = asyncio.create_task(self._cache_single_scenario(hand, opponents))
                tasks.append(task)
        
        # Run in smaller batches to avoid overwhelming the system
        batch_size = 5  # Much smaller batches
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            await asyncio.sleep(0.1)  # Longer delay to give user requests priority
            self._update_elapsed_time()
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Priority hands cached in {elapsed:.1f}s ({self.cache_stats['preflop_cached']} scenarios)")
        self._active_tasks -= 1
        self._check_warming_complete()
    
    async def _cache_single_scenario(self, hand, opponents):
        """Cache a single scenario asynchronously."""
        try:
            # Run the calculation in our dedicated cache thread pool
            # This prevents cache warming from blocking user requests
            loop = asyncio.get_event_loop()
            start_time = time.time()
            result = await loop.run_in_executor(self._cache_executor, self.calculator.calculate, hand, opponents)
            elapsed = time.time() - start_time
            
            # If calculation was very fast (< 5ms), it was likely cached
            was_cached = elapsed < 0.005
            
            if not was_cached:
                # This was a new calculation, increment both counters
                self.cache_stats['preflop_cached'] += 1
                self.cache_stats['new_cached'] += 1
            # If it was already cached, we don't increment the total count
                
        except Exception as e:
            logger.warning(f"Failed to cache {hand} vs {opponents}: {e}")
            self.cache_stats['errors'] += 1
    
    async def preload_all_preflop(self) -> None:
        """Preload all preflop scenarios in the background."""
        logger.info("🔄 Starting background preflop cache warming...")
        self._active_tasks += 1
        start_time = time.time()
        
        all_hands = self.generate_all_hands()
        
        # Process hands in very small chunks with async execution
        chunk_size = 3  # Very small chunks
        for i in range(0, len(all_hands), chunk_size):
            chunk = all_hands[i:i + chunk_size]
            
            tasks = []
            for hand in chunk:
                # Skip if it's a priority hand (already cached)
                hand_str = ''.join(hand)
                if any(''.join(ph) == hand_str for ph in self.PRIORITY_HANDS):
                    continue
                
                for opponents in range(1, 7):  # 1-6 opponents
                    task = asyncio.create_task(self._cache_single_scenario(hand, opponents))
                    tasks.append(task)
            
            # Run chunk in parallel
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Much longer sleep to ensure user requests get priority
            await asyncio.sleep(1.0)
            
            # Progress update every 500 calculations
            if self.cache_stats['preflop_cached'] % 500 == 0:
                elapsed = time.time() - start_time
                rate = self.cache_stats['preflop_cached'] / elapsed if elapsed > 0 else 0
                logger.info(f"📊 Progress: {self.cache_stats['preflop_cached']} preflop scenarios cached ({rate:.0f}/sec)")
        
        self.cache_stats['total_time'] = time.time() - start_time
        logger.info(f"✅ Preflop caching complete: {self.cache_stats['preflop_cached']} scenarios in {self.cache_stats['total_time']:.1f}s")
        self._active_tasks -= 1
        self._check_warming_complete()
    
    async def preload_common_boards(self) -> None:
        """Preload common board textures."""
        logger.info("🎲 Caching common board patterns...")
        self._active_tasks += 1
        
        # Common flop textures
        common_flops = [
            # Monotone flops
            ['A♠', 'K♠', 'Q♠'], ['K♥', 'Q♥', 'J♥'], ['Q♦', 'J♦', '10♦'],
            # Two-tone flops
            ['A♠', 'K♠', 'Q♥'], ['K♠', 'Q♠', 'J♥'], ['Q♠', 'J♠', '10♥'],
            # Rainbow flops
            ['A♠', 'K♥', 'Q♦'], ['K♠', 'Q♥', 'J♦'], ['Q♠', 'J♥', '10♦'],
            # Paired flops
            ['A♠', 'A♥', 'K♠'], ['K♠', 'K♥', 'Q♠'], ['Q♠', 'Q♥', 'J♠'],
            # Low flops
            ['9♠', '8♥', '7♦'], ['8♠', '7♥', '6♦'], ['7♠', '6♥', '5♦']
        ]
        
        # Cache with common hands vs common boards
        common_hands = self.PRIORITY_HANDS[:10]  # Top 10 priority hands
        
        tasks = []
        for board in common_flops:
            for hand in common_hands:
                # Skip if hand cards conflict with board
                if any(card in board for card in hand):
                    continue
                    
                for opponents in [1, 2, 3]:  # Most common opponent counts
                    task = asyncio.create_task(self._cache_board_scenario(hand, opponents, board))
                    tasks.append(task)
        
        # Process in batches
        batch_size = 15
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch, return_exceptions=True)
            await asyncio.sleep(0.2)  # Pause between batches
        
        logger.info(f"✅ Board caching complete: {self.cache_stats['board_cached']} scenarios")
        self._active_tasks -= 1
        self._check_warming_complete()
    
    async def _cache_board_scenario(self, hand, opponents, board):
        """Cache a single board scenario asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(self._cache_executor, self.calculator.calculate, hand, opponents, board)
            self.cache_stats['board_cached'] += 1
        except Exception as e:
            self.cache_stats['errors'] += 1
    
    async def initialize_cache(self, full_preload: bool = True) -> dict:
        """
        Initialize the cache system.
        
        Args:
            full_preload: If True, cache all preflop scenarios. If False, only priority hands.
            
        Returns:
            Cache statistics
        """
        logger.info("🏰 Initializing Camelot cache system...")
        start_time = time.time()
        self.cache_stats['start_time'] = start_time
        
        # Calculate total expected scenarios
        total_hands = len(self.generate_all_hands())  # 1326 unique hands
        total_preflop_scenarios = total_hands * 6  # 6 opponent counts (1-6)
        self.cache_stats['total_expected'] = total_preflop_scenarios
        
        # Try to get actual cache size from poker_knight if possible
        try:
            # Check if we can access the cache database directly
            import sqlite3
            cache_db_path = os.path.join(os.path.expanduser("~/.camelot_cache"), "poker_cache.db")
            
            if os.path.exists(cache_db_path):
                conn = sqlite3.connect(cache_db_path)
                cursor = conn.cursor()
                # Count entries in the cache_results table
                try:
                    cursor.execute("SELECT COUNT(*) FROM cache_results")
                    existing_count = cursor.fetchone()[0]
                except Exception as e:
                    logger.warning(f"Could not query cache_results table: {e}")
                    existing_count = 0
                conn.close()
                
                # Estimate preflop scenarios from total cache entries
                # This is approximate but better than starting from 0
                estimated_cached = min(existing_count, total_preflop_scenarios)
            else:
                estimated_cached = 0
        except Exception as e:
            logger.warning(f"Could not check existing cache: {e}")
            estimated_cached = 0
        
        self.cache_stats['initial_cached'] = estimated_cached
        self.cache_stats['preflop_cached'] = estimated_cached  # Start counting from existing
        
        logger.info(f"📊 Estimated {estimated_cached}/{total_preflop_scenarios} scenarios already cached")
        
        # Always show warming if not fully populated
        if estimated_cached < total_preflop_scenarios:
            self._is_warming = True
            
            # Start all caching tasks in background
            tasks = []
            
            # Priority hands task (if not already cached)
            if estimated_cached < len(self.PRIORITY_HANDS) * 6:
                tasks.append(asyncio.create_task(self.preload_priority_hands()))
            
            if full_preload:
                # Preload all preflop scenarios in background
                tasks.append(asyncio.create_task(self.preload_all_preflop()))
            
            # Always preload common boards
            tasks.append(asyncio.create_task(self.preload_common_boards()))
            
            logger.info("🚀 Cache warming started in background...")
            
            return {
                'status': 'warming',
                'scenarios_cached': estimated_cached,
                'total_scenarios': total_preflop_scenarios,
                'startup_time': time.time() - start_time,
                'background_tasks': len(tasks)
            }
        else:
            # Cache fully populated
            logger.info("✅ Cache fully populated from previous sessions")
            self._is_warming = False
            
            return {
                'status': 'ready',
                'scenarios_cached': total_preflop_scenarios,
                'total_scenarios': total_preflop_scenarios,
                'startup_time': time.time() - start_time,
                'background_tasks': 0
            }
    
    def get_cache_stats(self) -> dict:
        """Get current cache statistics."""
        self._update_elapsed_time()
        return self.cache_stats.copy()
    
    def is_warming(self) -> bool:
        """Check if cache warming is currently active."""
        return self._is_warming
    
    def _update_elapsed_time(self):
        """Update elapsed time if warming is active."""
        if self._is_warming and self.cache_stats['start_time']:
            self.cache_stats['elapsed_time'] = time.time() - self.cache_stats['start_time']
    
    def _check_warming_complete(self):
        """Check if all warming tasks are complete."""
        if self._active_tasks == 0:
            self._is_warming = False
            self._update_elapsed_time()
            logger.info("🎉 Cache warming complete!")