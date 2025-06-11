"""
Cached poker calculator that wraps the base PokerCalculator with caching.
"""

from typing import List, Dict, Optional
import time
from .poker_logic import PokerCalculator
from .cache_storage import CacheStorage
from .cache_key_generator import CacheKeyGenerator


class CachedPokerCalculator(PokerCalculator):
    """Poker calculator with integrated caching layer."""
    
    def __init__(self, cache_storage: Optional[CacheStorage] = None):
        """
        Initialize cached calculator.
        
        Args:
            cache_storage: Cache storage instance (creates default if None)
        """
        super().__init__()
        self.cache = cache_storage or CacheStorage()
        self._cache_enabled = True
    
    def calculate(
        self,
        hero_hand: List[str],
        num_opponents: int,
        board_cards: Optional[List[str]] = None,
        simulation_mode: str = "default",
        hero_position: Optional[str] = None,
        stack_sizes: Optional[List[int]] = None,
        pot_size: Optional[int] = None
    ) -> Dict:
        """
        Calculate poker hand probabilities with caching.
        
        Dynamic parameters (position, stacks, pot) don't affect cache key
        but are applied to results after cache retrieval.
        
        Args:
            hero_hand: List of 2 cards for hero
            num_opponents: Number of opponents (1-6)
            board_cards: Optional list of 3-5 community cards
            simulation_mode: "fast", "default", or "precision"
            hero_position: Optional position (not cached)
            stack_sizes: Optional stack sizes (not cached)
            pot_size: Optional pot size (not cached)
        
        Returns:
            Dictionary with calculation results
        """
        # Validate inputs first
        is_valid, error_msg = self.validate_hand(hero_hand, board_cards)
        if not is_valid:
            raise ValueError(error_msg)
        
        if not 1 <= num_opponents <= 6:
            raise ValueError("Number of opponents must be between 1 and 6")
        
        if simulation_mode not in ["fast", "default", "precision"]:
            raise ValueError("Simulation mode must be 'fast', 'default', or 'precision'")
        
        # Generate cache key (excluding dynamic parameters)
        cache_key = CacheKeyGenerator.generate_key(
            hero_hand, num_opponents, board_cards, simulation_mode
        )
        
        # Check if we have any dynamic parameters
        has_dynamic_params = (hero_position is not None or 
                            stack_sizes is not None or 
                            pot_size is not None)
        
        # Try to get from cache if no dynamic params or cache enabled
        cached_result = None
        if self._cache_enabled and not has_dynamic_params:
            start_time = time.time()
            cached_result = self.cache.get(cache_key)
            cache_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if cached_result:
                # Validate cached result has all required fields
                is_valid = self._validate_cached_result(cached_result)
                
                if not is_valid:
                    # Stale cache entry, recalculate
                    # Don't count as a hit since we're recalculating
                    pass
                else:
                    # Valid cache entry
                    # Add cache metadata
                    cached_result['from_cache'] = True
                    cached_result['cache_time_ms'] = cache_time
                    # Override execution time to show cache retrieval time
                    cached_result['execution_time_ms'] = cache_time
                    # Override computation source for cached results
                    cached_result['gpu_used'] = False
                    cached_result['backend'] = 'cache'
                    cached_result['device'] = None
                    return cached_result
        
        # Calculate if not cached or has dynamic params
        start_time = time.time()
        result = super().calculate(
            hero_hand, num_opponents, board_cards, 
            simulation_mode, hero_position, stack_sizes, pot_size
        )
        calc_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Cache the result if no dynamic params
        if self._cache_enabled and not has_dynamic_params:
            # Create cache metadata
            metadata = CacheKeyGenerator.create_metadata(
                hero_hand, num_opponents, board_cards, simulation_mode
            )
            
            # Store in cache
            self.cache.set(
                cache_key, result,
                metadata['hero_hand'],
                metadata['num_opponents'],
                metadata['board_cards'],
                metadata['simulation_mode']
            )
        
        # Add timing metadata
        result['from_cache'] = False
        result['calculation_time_ms'] = calc_time
        
        return result
    
    def calculate_no_cache(
        self,
        hero_hand: List[str],
        num_opponents: int,
        board_cards: Optional[List[str]] = None,
        simulation_mode: str = "default",
        **kwargs
    ) -> Dict:
        """Calculate without using cache (for testing/comparison)."""
        self._cache_enabled = False
        try:
            result = self.calculate(
                hero_hand, num_opponents, board_cards, 
                simulation_mode, **kwargs
            )
            return result
        finally:
            self._cache_enabled = True
    
    def _validate_cached_result(self, result: Dict) -> bool:
        """
        Validate that a cached result has all required fields.
        
        Args:
            result: Cached result dictionary
            
        Returns:
            True if valid, False if missing required data
        """
        # Required fields that must exist and not be None
        required_fields = [
            'win_probability',
            'tie_probability', 
            'loss_probability',
            'simulations_run',
            'execution_time_ms',
            'confidence_interval'
        ]
        
        # Check required fields
        for field in required_fields:
            if field not in result or result[field] is None:
                return False
        
        # Check that hand_categories field exists (can be empty for pre-flop)
        if 'hand_categories' not in result:
            return False
        
        # Additional validation for confidence_interval
        ci = result.get('confidence_interval')
        if not isinstance(ci, (list, tuple)) or len(ci) != 2:
            return False
        
        return True
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        return self.cache.get_stats()
    
    def clear_invalid_cache_entries(self):
        """Clear cache entries with empty hand_categories."""
        try:
            count = self.cache.clear_invalid_entries()
            return count
        except Exception as e:
            return 0
    
    def clear_cache(self, memory_only: bool = False):
        """
        Clear cache.
        
        Args:
            memory_only: If True, only clear memory cache
        """
        if memory_only:
            self.cache.clear_memory_cache()
        else:
            self.cache.clear_all()
    
    def warm_cache_for_hand(self, hero_hand: List[str], simulation_mode: str = "default"):
        """
        Warm cache for a specific hand across all scenarios.
        
        Args:
            hero_hand: Hero's hand to cache
            simulation_mode: Simulation mode to use
        """
        # Cache preflop for all opponent counts
        for num_opponents in range(1, 7):
            try:
                self.calculate(hero_hand, num_opponents, None, simulation_mode)
            except Exception as e:
                print(f"Error caching {hero_hand} vs {num_opponents}: {e}")
    
    def warm_cache_for_board(self, hero_hand: List[str], board_cards: List[str], 
                           simulation_mode: str = "default"):
        """
        Warm cache for a specific hand and board.
        
        Args:
            hero_hand: Hero's hand
            board_cards: Board cards (3-5 cards)
            simulation_mode: Simulation mode
        """
        # Cache for all opponent counts
        for num_opponents in range(1, 7):
            try:
                self.calculate(hero_hand, num_opponents, board_cards, simulation_mode)
            except Exception as e:
                print(f"Error caching {hero_hand} on {board_cards}: {e}")