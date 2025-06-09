"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Tuple, Union, Any
from pydantic import BaseModel, Field, field_validator


class CalculateRequest(BaseModel):
    """Request model for poker calculation."""
    hero_hand: List[str] = Field(..., description="Hero's two hole cards", min_length=2, max_length=2)
    num_opponents: int = Field(..., description="Number of opponents", ge=1, le=6)
    board_cards: Optional[List[str]] = Field(None, description="Community cards (3-5 cards)", min_length=3, max_length=5)
    simulation_mode: str = Field("default", description="Simulation mode: fast, default, or precision")
    hero_position: Optional[str] = Field(None, description="Hero's position: button, sb, bb, utg, utg+1, mp, mp+1, co")
    stack_sizes: Optional[List[int]] = Field(None, description="Stack sizes in big blinds [hero, opp1, opp2, ...]")
    pot_size: Optional[int] = Field(None, description="Current pot size in big blinds")
    
    @field_validator('hero_hand', 'board_cards')
    @classmethod
    def validate_cards(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Basic validation of card format."""
        if v is None:
            return v
        
        for card in v:
            if not isinstance(card, str) or len(card) < 2:
                raise ValueError(f"Invalid card format: {card}")
        
        return v
    
    @field_validator('simulation_mode')
    @classmethod
    def validate_simulation_mode(cls, v: str) -> str:
        """Validate simulation mode."""
        valid_modes = ["fast", "default", "precision"]
        if v not in valid_modes:
            raise ValueError(f"Simulation mode must be one of: {', '.join(valid_modes)}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "hero_hand": ["A♠", "K♠"],
                    "num_opponents": 2,
                    "board_cards": ["Q♠", "J♦", "10♥"],
                    "simulation_mode": "default"
                }
            ]
        }
    }


class CalculateResponse(BaseModel):
    """Response model for poker calculation."""
    success: bool = Field(..., description="Whether the calculation succeeded")
    win_probability: Optional[float] = Field(None, description="Probability of winning")
    tie_probability: Optional[float] = Field(None, description="Probability of tying")
    loss_probability: Optional[float] = Field(None, description="Probability of losing")
    simulations_run: Optional[int] = Field(None, description="Number of simulations performed")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")
    confidence_interval: Optional[Tuple[float, float]] = Field(None, description="95% confidence interval")
    hand_categories: Optional[Dict[str, float]] = Field(None, description="Frequency of hand categories")
    hero_hand: List[str] = Field(..., description="Hero's cards used in calculation")
    board_cards: List[str] = Field(..., description="Board cards used in calculation")
    num_opponents: int = Field(..., description="Number of opponents in calculation")
    error: Optional[str] = Field(None, description="Error message if calculation failed")
    
    # Advanced features (optional, for future use)
    position_aware_equity: Optional[Dict[str, float]] = Field(None, description="Position-based equity adjustments")
    icm_equity: Optional[float] = Field(None, description="ICM-adjusted equity for tournaments")
    multi_way_statistics: Optional[Dict[str, Any]] = Field(None, description="Statistics for multi-way pots")
    defense_frequencies: Optional[Dict[str, float]] = Field(None, description="Optimal defense frequencies")
    coordination_effects: Optional[Dict[str, float]] = Field(None, description="Board/range coordination effects")
    stack_to_pot_ratio: Optional[float] = Field(None, description="Stack-to-Pot Ratio for tournament play")
    tournament_pressure: Optional[Dict[str, float]] = Field(None, description="Tournament pressure metrics")
    fold_equity_estimates: Optional[Dict[str, float]] = Field(None, description="Position-based fold equity estimates")
    bubble_factor: Optional[float] = Field(None, description="ICM bubble factor adjustments")
    bluff_catching_frequency: Optional[float] = Field(None, description="Optimal bluff-catching frequency")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "win_probability": 0.823,
                    "tie_probability": 0.012,
                    "loss_probability": 0.165,
                    "simulations_run": 100000,
                    "execution_time_ms": 125.4,
                    "confidence_interval": [0.820, 0.826],
                    "hand_categories": {
                        "high_card": 0.174,
                        "pair": 0.438,
                        "two_pair": 0.235,
                        "three_of_a_kind": 0.048,
                        "straight": 0.046,
                        "flush": 0.030,
                        "full_house": 0.026,
                        "four_of_a_kind": 0.002,
                        "straight_flush": 0.001,
                        "royal_flush": 0.000
                    },
                    "hero_hand": ["A♠", "K♠"],
                    "board_cards": ["Q♠", "J♦", "10♥"],
                    "num_opponents": 2,
                    "error": None
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    poker_knight_available: bool = Field(..., description="Whether poker_knight module is available")