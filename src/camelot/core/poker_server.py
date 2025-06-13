"""
Poker Knight NG Server Management
Provides singleton server instance with GPU keep-alive and health monitoring.
"""

import atexit
import logging
import threading
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PokerServerManager:
    """Singleton manager for poker_knight_ng server with GPU keep-alive."""
    
    _instance = None
    _lock = threading.Lock()
    _server = None
    _is_cold = True
    _stats = {
        'total_calculations': 0,
        'cold_starts': 0,
        'warm_calculations': 0,
        'total_time_ms': 0.0,
        'warm_time_ms': 0.0,
        'server_created_at': None,
        'last_calculation_at': None
    }
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize_server()
        return cls._instance
    
    def _initialize_server(self):
        """Initialize the poker server with GPU keep-alive."""
        try:
            from poker_knight_ng import create_poker_server
            
            logger.info("Initializing poker_knightNG server with GPU keep-alive...")
            self._server = create_poker_server(
                keep_alive_seconds=60.0,  # Keep GPU warm for 60 seconds
                auto_warmup=True  # Automatically warm up GPU on creation
            )
            
            self._stats['server_created_at'] = datetime.now()
            self._is_cold = True
            
            # Register cleanup handler
            atexit.register(self._shutdown_server)
            
            logger.info("Poker server initialized successfully with 60s keep-alive")
            
        except Exception as e:
            logger.error(f"Failed to initialize poker server: {e}")
            raise
    
    def _shutdown_server(self):
        """Gracefully shutdown the server."""
        if self._server:
            try:
                logger.info("Shutting down poker server...")
                if hasattr(self._server, 'shutdown'):
                    self._server.shutdown()
                logger.info("Poker server shutdown complete")
            except AttributeError as e:
                # Server might not have shutdown method, that's okay
                logger.debug(f"Server shutdown method not available: {e}")
            except Exception as e:
                logger.error(f"Error during server shutdown: {e}")
    
    def solve(self, hero_hand: List[str], num_opponents: int, 
             board_cards: Optional[List[str]] = None, **kwargs) -> Any:
        """
        Solve a single poker problem using the server.
        
        Args:
            hero_hand: Hero's 2 cards
            num_opponents: Number of opponents (1-6)
            board_cards: Optional community cards
            **kwargs: Additional parameters (simulation_mode, position, etc.)
        
        Returns:
            SimulationResult object
        """
        if not self._server:
            raise RuntimeError("Poker server not initialized")
        
        start_time = time.time()
        
        try:
            # Call server solve method
            result = self._server.solve(hero_hand, num_opponents, board_cards, **kwargs)
            
            # Update statistics
            execution_time_ms = (time.time() - start_time) * 1000
            self._update_stats(execution_time_ms)
            
            # Add cold/warm indicator to result
            result._is_cold_start = self._is_cold
            
            # Mark as warm after first solve
            if self._is_cold:
                logger.info(f"Cold start calculation completed in {execution_time_ms:.2f}ms")
                self._is_cold = False
            else:
                logger.debug(f"Warm calculation completed in {execution_time_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Server solve failed: {e}")
            raise
    
    def solve_batch(self, problems: List[Dict[str, Any]]) -> List[Optional[Any]]:
        """
        Solve multiple poker problems in batch.
        
        Args:
            problems: List of problem dictionaries with solve parameters
        
        Returns:
            List of SimulationResult objects (None for invalid inputs)
        """
        if not self._server:
            raise RuntimeError("Poker server not initialized")
        
        start_time = time.time()
        
        try:
            # Process batch
            results = self._server.solve_batch(problems)
            
            # Update statistics for batch
            execution_time_ms = (time.time() - start_time) * 1000
            self._update_stats(execution_time_ms, batch_size=len(problems))
            
            # Mark cold/warm for each result
            for result in results:
                if result is not None:
                    result._is_cold_start = self._is_cold
            
            if self._is_cold:
                logger.info(f"Cold start batch ({len(problems)} problems) completed in {execution_time_ms:.2f}ms")
                self._is_cold = False
            else:
                logger.debug(f"Warm batch ({len(problems)} problems) completed in {execution_time_ms:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"Batch solve failed: {e}")
            raise
    
    def _update_stats(self, execution_time_ms: float, batch_size: int = 1):
        """Update internal statistics."""
        self._stats['total_calculations'] += batch_size
        self._stats['total_time_ms'] += execution_time_ms
        self._stats['last_calculation_at'] = datetime.now()
        
        if self._is_cold:
            self._stats['cold_starts'] += 1
        else:
            self._stats['warm_calculations'] += batch_size
            self._stats['warm_time_ms'] += execution_time_ms
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get server statistics and health information.
        
        Returns:
            Dictionary with server stats and GPU keep-alive status
        """
        stats = self._stats.copy()
        
        # Calculate averages
        if stats['warm_calculations'] > 0:
            stats['average_warm_time_ms'] = stats['warm_time_ms'] / stats['warm_calculations']
        else:
            stats['average_warm_time_ms'] = 0.0
        
        if stats['total_calculations'] > 0:
            stats['average_total_time_ms'] = stats['total_time_ms'] / stats['total_calculations']
        else:
            stats['average_total_time_ms'] = 0.0
        
        # Add server-specific stats if available
        if self._server and hasattr(self._server, 'get_statistics'):
            stats['server_stats'] = self._server.get_statistics()
        
        # Add GPU keep-alive status
        stats['is_gpu_warm'] = not self._is_cold
        stats['keep_alive_seconds'] = 60.0
        
        return stats
    
    def is_cold_start(self) -> bool:
        """Check if the next calculation will be a cold start."""
        return self._is_cold
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the server.
        
        Returns:
            Health status dictionary
        """
        health = {
            'status': 'unknown',
            'server_initialized': self._server is not None,
            'is_cold': self._is_cold,
            'uptime_seconds': 0,
            'last_calculation_seconds_ago': None
        }
        
        if self._stats['server_created_at']:
            health['uptime_seconds'] = (datetime.now() - self._stats['server_created_at']).total_seconds()
        
        if self._stats['last_calculation_at']:
            health['last_calculation_seconds_ago'] = (datetime.now() - self._stats['last_calculation_at']).total_seconds()
        
        # Try a simple calculation to verify server is responsive
        if self._server:
            try:
                test_result = self._server.solve(['A♠', 'A♥'], 1)
                if test_result and hasattr(test_result, 'win_probability'):
                    health['status'] = 'healthy'
                else:
                    health['status'] = 'unhealthy'
            except Exception as e:
                health['status'] = 'error'
                health['error'] = str(e)
        else:
            health['status'] = 'not_initialized'
        
        return health
    
    def session(self):
        """
        Create a session context for grouped calculations.
        
        Usage:
            with server.session():
                result1 = server.solve(...)
                result2 = server.solve(...)
        """
        if not self._server:
            raise RuntimeError("Poker server not initialized")
        
        return self._server.session()


# Global instance getter
_server_instance = None

def get_poker_server() -> PokerServerManager:
    """Get the global poker server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = PokerServerManager()
    return _server_instance