"""
Cache manager for preloading poker calculations at startup.
Works with CachedPokerCalculator to warm the cache.
Now leverages poker_knightNG's GPU keep-alive for efficient warming.
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
        
        # Track recent cache additions for rate calculation
        self._recent_cache_times = []  # List of (timestamp, count) tuples
        self._last_count = 0
        
        # Create a separate thread pool for cache warming
        # Can use more threads now with GPU keep-alive efficiency
        self._cache_executor = ThreadPoolExecutor(
            max_workers=4,  # Increased from 2 to 4 for faster warming
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
            result = await loop.run_in_executor(self._cache_executor, self.calculator.calculate, hand, opponents)
            
            # Check if this was a cache hit using the new cache system
            was_cached = result.get('from_cache', False)
            
            # Also check if it was a cold start (ignore cold starts for performance metrics)
            is_cold_start = result.get('_is_cold_start', False)
            
            if not was_cached and not is_cold_start:
                # This was a new calculation (not from cache, not cold start)
                self.cache_stats['preflop_cached'] += 1
                self.cache_stats['new_cached'] += 1
                self.cache_stats['warming_this_session'] += 1
            elif not was_cached and is_cold_start:
                # Cold start - still count it but note it separately
                self.cache_stats['preflop_cached'] += 1
                self.cache_stats['new_cached'] += 1
                self.cache_stats['warming_this_session'] += 1
                logger.debug(f"Cold start for {hand} vs {opponents}")
            # If it was already cached, we don't increment the total count
                
        except Exception as e:
            logger.warning(f"Failed to cache {hand} vs {opponents}: {e}")
            self.cache_stats['errors'] += 1
    
    async def _cache_batch_scenarios(self, problems):
        """Cache a batch of scenarios using batch API for efficiency."""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self._cache_executor, 
                self.calculator.calculate_batch, 
                problems
            )
            
            # Count successful new calculations
            for result in results:
                if result and not result.get('from_cache', False):
                    if not result.get('_is_cold_start', False):
                        self.cache_stats['preflop_cached'] += 1
                        self.cache_stats['new_cached'] += 1
                        self.cache_stats['warming_this_session'] += 1
                        
        except Exception as e:
            logger.warning(f"Failed to cache batch: {e}")
            self.cache_stats['errors'] += len(problems)
    
    async def preload_all_preflop(self) -> None:
        """Preload all preflop scenarios in the background."""
        logger.info("🔄 Starting background preflop cache warming...")
        self._active_tasks += 1
        start_time = time.time()
        
        all_hands = self.generate_all_hands()
        
        # Process hands in moderate chunks to leverage GPU keep-alive
        # Larger chunks now that we have GPU warmth
        chunk_size = 10  # Increased chunk size
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
            
            # Shorter sleep now that GPU is warm (calculations are faster)
            await asyncio.sleep(0.2)
            
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
            result = await loop.run_in_executor(self._cache_executor, self.calculator.calculate, hand, opponents, board)
            
            # Check if this was a cache hit using the new cache system
            was_cached = result.get('from_cache', False)
            
            if not was_cached:
                self.cache_stats['board_cached'] += 1
                self.cache_stats['warming_this_session'] += 1
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
        
        # Log GPU status
        try:
            if hasattr(self.calculator, 'get_server_statistics'):
                server_stats = self.calculator.get_server_statistics()
                if server_stats.get('is_gpu_warm'):
                    logger.info("🔥 GPU is already warm, cache warming will be faster")
                else:
                    logger.info("❄️ GPU is cold, first calculations will be slower")
        except Exception:
            pass  # Server stats not available, continue anyway
        
        # Try to get actual cache size from our new cache system
        try:
            # Get cache stats from the calculator (which uses our new cache)
            if hasattr(self.calculator, 'get_cache_stats'):
                cache_stats = self.calculator.get_cache_stats()
                existing_count = cache_stats.get('sqlite_entries', 0)
                
                # Count only preflop scenarios (no board cards)
                # This is approximate but better than starting from 0
                estimated_cached = min(existing_count, total_preflop_scenarios)
            else:
                estimated_cached = 0
        except Exception as e:
            logger.warning(f"Could not check existing cache: {e}")
            estimated_cached = 0
        
        self.cache_stats['initial_cached'] = estimated_cached
        self.cache_stats['preflop_cached'] = estimated_cached  # Start counting from existing
        self.cache_stats['warming_this_session'] = 0  # Track new entries added this session
        
        logger.info(f"📊 Found {estimated_cached}/{total_preflop_scenarios} scenarios already cached")
        
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
        stats = self.cache_stats.copy()
        
        # Calculate rolling rate (entries in the last 60 seconds)
        stats['rolling_rate'] = self._calculate_rolling_rate()
        
        return stats
    
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
    
    def _calculate_rolling_rate(self) -> float:
        """Calculate the rolling cache rate over the last 60 seconds."""
        current_time = time.time()
        # Track new entries this session, not total count
        current_count = self.cache_stats['warming_this_session']
        
        # Add current data point
        self._recent_cache_times.append((current_time, current_count))
        
        # Remove data points older than 60 seconds
        cutoff_time = current_time - 60
        self._recent_cache_times = [(t, c) for t, c in self._recent_cache_times if t > cutoff_time]
        
        # Need at least 2 points to calculate rate
        if len(self._recent_cache_times) < 2:
            return 0.0
        
        # Calculate rate based on first and last points in the window
        oldest_time, oldest_count = self._recent_cache_times[0]
        newest_time, newest_count = self._recent_cache_times[-1]
        
        time_diff = newest_time - oldest_time
        count_diff = newest_count - oldest_count
        
        if time_diff > 0:
            return count_diff / time_diff  # Rate per second
        return 0.0
    
    def reset_stats(self):
        """Reset cache statistics (for debugging)."""
        self.cache_stats = {
            'preflop_cached': 0,
            'board_cached': 0,
            'total_time': 0,
            'errors': 0,
            'start_time': None,
            'elapsed_time': 0,
            'initial_cached': 0,
            'new_cached': 0,
            'total_expected': 7956,
            'warming_this_session': 0,
            'rolling_rate': 0
        }
        self._recent_cache_times = []
        self._is_warming = False