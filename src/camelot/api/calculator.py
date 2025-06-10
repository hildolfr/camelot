"""Calculator API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Optional

from ..core.cache_init import get_cached_calculator, get_cache_manager
from .models import CalculateRequest, CalculateResponse, HealthResponse


router = APIRouter(prefix="/api", tags=["calculator"])
calculator = get_cached_calculator()
cache_manager: Optional['CacheManager'] = None


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict:
    """Check if the API is healthy and poker_knight is available."""
    try:
        # Try a simple calculation to verify poker_knight works
        test_result = calculator.calculate_no_cache(["A♠", "K♠"], 1)
        poker_available = True
    except:
        poker_available = False
    
    return {
        "status": "healthy",
        "version": "0.0.1",
        "poker_knight_available": poker_available
    }


@router.post("/calculate", response_model=CalculateResponse)
async def calculate_poker_odds(request: CalculateRequest) -> Dict:
    """
    Calculate poker hand probabilities.
    
    This endpoint accepts hero's hole cards, number of opponents, and optional board cards,
    then returns win/tie/loss probabilities along with detailed statistics.
    """
    try:
        # Call calculate method directly
        result = calculator.calculate(
            request.hero_hand,
            request.num_opponents,
            request.board_cards,
            request.simulation_mode,
            request.hero_position,
            request.stack_sizes,
            request.pot_size
        )
        
        
        # Build response with all available fields
        response_data = {
            "success": True,
            "win_probability": result.get("win_probability"),
            "tie_probability": result.get("tie_probability"),
            "loss_probability": result.get("loss_probability"),
            "simulations_run": result.get("simulations_run"),
            "execution_time_ms": result.get("execution_time_ms"),
            "confidence_interval": result.get("confidence_interval"),
            "hand_categories": result.get("hand_categories"),
            "hero_hand": result.get("hero_hand"),
            "board_cards": result.get("board_cards"),
            "num_opponents": result.get("num_opponents"),
            "error": None
        }
        
        # Add any advanced features if present
        for key in ["position_aware_equity", "icm_equity", "multi_way_statistics", 
                    "defense_frequencies", "coordination_effects", "stack_to_pot_ratio",
                    "tournament_pressure", "fold_equity_estimates", "bubble_factor",
                    "bluff_catching_frequency", "from_cache", "backend", "gpu_used", 
                    "device", "cache_time_ms", "calculation_time_ms"]:
            if key in result:
                response_data[key] = result[key]
        
        return response_data
        
    except ValueError as e:
        # Return error response for validation errors
        return {
            "success": False,
            "win_probability": None,
            "tie_probability": None,
            "loss_probability": None,
            "simulations_run": None,
            "execution_time_ms": None,
            "confidence_interval": None,
            "hand_categories": None,
            "hero_hand": request.hero_hand,
            "board_cards": request.board_cards or [],
            "num_opponents": request.num_opponents,
            "error": str(e)
        }
        
    except Exception as e:
        # Unexpected errors
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/cache-status")
async def get_cache_status() -> Dict:
    """Get current cache statistics."""
    # Get cache stats directly from calculator
    cache_stats = calculator.get_cache_stats()
    
    # Get warming stats from cache manager if available
    if cache_manager:
        warming_stats = cache_manager.get_cache_stats()
        # Show what's being warmed this session, not the total count
        warming_this_session = warming_stats.get('warming_this_session', 0)
        initial_cached = warming_stats.get('initial_cached', 0)
        total_expected = warming_stats.get('total_expected', 0)
        rate = warming_stats.get('rolling_rate', 0)
        is_warming = cache_manager.is_warming()
        
        # Calculate progress
        progress_percent = ((initial_cached + warming_this_session) / total_expected * 100) if total_expected > 0 else 0
    else:
        warming_this_session = 0
        initial_cached = cache_stats.get('sqlite_entries', 0)
        total_expected = 0
        rate = 0
        is_warming = False
        progress_percent = 0
    
    return {
        "status": "active",
        "is_warming": is_warming,
        "warming_this_session": warming_this_session,
        "initial_cached": initial_cached,
        "total_expected": total_expected,
        "progress_percent": round(progress_percent, 1),
        "rate_per_second": round(rate, 1),
        "statistics": {
            **cache_stats,
            "warming": warming_stats if cache_manager else {}
        }
    }


@router.post("/cache-reset")
async def reset_cache() -> Dict:
    """Reset the cache (debugging feature)."""
    try:
        # Clear the cache
        calculator.clear_cache()
        
        # Reset cache manager stats if available
        if cache_manager:
            cache_manager.reset_stats()
        
        return {
            "status": "success",
            "message": "Cache has been reset"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset cache: {str(e)}")