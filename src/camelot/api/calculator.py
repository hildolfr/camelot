"""Calculator API endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict

from ..core.poker_logic import PokerCalculator
from .models import CalculateRequest, CalculateResponse, HealthResponse


router = APIRouter(prefix="/api", tags=["calculator"])
calculator = PokerCalculator()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> Dict:
    """Check if the API is healthy and poker_knight is available."""
    try:
        # Try a simple calculation to verify poker_knight works
        test_result = calculator.calculate(["A♠", "K♠"], 1)
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
        result = calculator.calculate(
            hero_hand=request.hero_hand,
            num_opponents=request.num_opponents,
            board_cards=request.board_cards,
            simulation_mode=request.simulation_mode
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
                    "defense_frequencies", "coordination_effects"]:
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