"""Pydantic models for API requests and responses."""

from typing import List, Optional, Dict, Tuple, Union, Any
from pydantic import BaseModel, Field, field_validator


class CalculateRequest(BaseModel):
    """Request model for poker calculation with poker_knightNG parameters."""
    hero_hand: List[str] = Field(..., description="Hero's two hole cards", min_length=2, max_length=2)
    num_opponents: int = Field(..., description="Number of opponents", ge=1, le=6)
    board_cards: Optional[List[str]] = Field(None, description="Community cards (3-5 cards)", min_length=3, max_length=5)
    simulation_mode: str = Field("default", description="Simulation mode: fast, default, or precision")
    hero_position: Optional[str] = Field(None, description="Hero's position: early, middle, late, button, sb, bb")
    stack_sizes: Optional[List[int]] = Field(None, description="Stack sizes [hero, opp1, opp2, ...]")
    pot_size: Optional[int] = Field(None, description="Current pot size")
    
    # New poker_knightNG parameters
    tournament_context: Optional[Dict[str, Any]] = Field(None, description="Tournament info for ICM calculations")
    action_to_hero: Optional[str] = Field(None, description="Current action: check, bet, raise, reraise")
    bet_size: Optional[float] = Field(None, description="Current bet size relative to pot (e.g., 0.5 for half-pot)")
    street: Optional[str] = Field(None, description="Current street: preflop, flop, turn, river")
    players_to_act: Optional[int] = Field(None, description="Number of players still to act after hero")
    tournament_stage: Optional[str] = Field(None, description="Tournament stage: early, middle, bubble, final_table")
    blind_level: Optional[int] = Field(None, description="Current blind level for tournament pressure")
    
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
    
    @field_validator('hero_position')
    @classmethod
    def validate_position(cls, v: Optional[str]) -> Optional[str]:
        """Validate hero position."""
        if v is None:
            return v
        valid_positions = ["early", "middle", "late", "button", "sb", "bb"]
        if v not in valid_positions:
            raise ValueError(f"Position must be one of: {', '.join(valid_positions)}")
        return v
    
    @field_validator('action_to_hero')
    @classmethod
    def validate_action(cls, v: Optional[str]) -> Optional[str]:
        """Validate action to hero."""
        if v is None:
            return v
        valid_actions = ["check", "bet", "raise", "reraise"]
        if v not in valid_actions:
            raise ValueError(f"Action must be one of: {', '.join(valid_actions)}")
        return v
    
    @field_validator('street')
    @classmethod
    def validate_street(cls, v: Optional[str]) -> Optional[str]:
        """Validate street."""
        if v is None:
            return v
        valid_streets = ["preflop", "flop", "turn", "river"]
        if v not in valid_streets:
            raise ValueError(f"Street must be one of: {', '.join(valid_streets)}")
        return v
    
    @field_validator('tournament_stage')
    @classmethod
    def validate_tournament_stage(cls, v: Optional[str]) -> Optional[str]:
        """Validate tournament stage."""
        if v is None:
            return v
        valid_stages = ["early", "middle", "bubble", "final_table"]
        if v not in valid_stages:
            raise ValueError(f"Tournament stage must be one of: {', '.join(valid_stages)}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "hero_hand": ["A♠", "K♠"],
                    "num_opponents": 2,
                    "board_cards": ["Q♠", "J♦", "10♥"],
                    "simulation_mode": "default",
                    "hero_position": "button",
                    "action_to_hero": "bet",
                    "bet_size": 0.5,
                    "street": "flop"
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
    
    # Advanced features from poker_knightNG
    position_aware_equity: Optional[Dict[str, float]] = Field(None, description="Position-based equity adjustments")
    icm_equity: Optional[float] = Field(None, description="ICM-adjusted equity for tournaments")
    multi_way_statistics: Optional[Dict[str, Any]] = Field(None, description="Statistics for multi-way pots")
    defense_frequencies: Optional[Dict[str, float]] = Field(None, description="Optimal defense frequencies")
    coordination_effects: Optional[Dict[str, float]] = Field(None, description="Board/range coordination effects")
    stack_to_pot_ratio: Optional[float] = Field(None, description="Stack-to-Pot Ratio for tournament play")
    tournament_pressure: Optional[Dict[str, Any]] = Field(None, description="Tournament pressure metrics")
    fold_equity_estimates: Optional[Dict[str, float]] = Field(None, description="Position-based fold equity estimates")
    bubble_factor: Optional[float] = Field(None, description="ICM bubble factor adjustments")
    bluff_catching_frequency: Optional[float] = Field(None, description="Optimal bluff-catching frequency")
    range_coordination_score: Optional[float] = Field(None, description="Range coordination score")
    
    # New poker_knightNG analysis fields
    spr: Optional[float] = Field(None, description="Stack-to-pot ratio for commitment decisions")
    pot_odds: Optional[float] = Field(None, description="Odds being offered by current bet")
    mdf: Optional[float] = Field(None, description="Minimum defense frequency against bet size")
    equity_needed: Optional[float] = Field(None, description="Breakeven equity required to call")
    commitment_threshold: Optional[float] = Field(None, description="SPR where hero is pot-committed")
    nuts_possible: Optional[List[str]] = Field(None, description="Possible nut hands on current board")
    draw_combinations: Optional[Dict[str, int]] = Field(None, description="Count of flush/straight draws")
    board_texture_score: Optional[float] = Field(None, description="Board texture score 0.0-1.0 (dry to wet)")
    equity_vs_range_percentiles: Optional[Dict[str, float]] = Field(None, description="Hero equity vs top X% of hands")
    positional_advantage_score: Optional[float] = Field(None, description="Quantified positional value")
    hand_vulnerability: Optional[float] = Field(None, description="Likelihood of being outdrawn")
    
    # Caching and computation metadata
    from_cache: Optional[bool] = Field(None, description="Whether result was retrieved from cache")
    cache_time_ms: Optional[float] = Field(None, description="Time to retrieve from cache in milliseconds")
    calculation_time_ms: Optional[float] = Field(None, description="Time to calculate result in milliseconds")
    
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


class BatchCalculateRequest(BaseModel):
    """Request model for batch poker calculations."""
    problems: List[CalculateRequest] = Field(..., description="List of poker problems to solve", min_length=1, max_length=100)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "problems": [
                        {
                            "hero_hand": ["A♠", "A♥"],
                            "num_opponents": 1,
                            "simulation_mode": "fast"
                        },
                        {
                            "hero_hand": ["K♠", "K♥"],
                            "num_opponents": 2,
                            "board_cards": ["Q♦", "7♣", "2♥"]
                        }
                    ]
                }
            ]
        }
    }


class BatchCalculateResponse(BaseModel):
    """Response model for batch poker calculations."""
    success: bool = Field(..., description="Whether all calculations succeeded")
    results: List[Optional[CalculateResponse]] = Field(..., description="List of results (None for failed calculations)")
    total_problems: int = Field(..., description="Total number of problems submitted")
    successful_calculations: int = Field(..., description="Number of successful calculations")
    total_execution_time_ms: float = Field(..., description="Total execution time for batch")
    average_execution_time_ms: float = Field(..., description="Average execution time per calculation")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    poker_knight_available: bool = Field(..., description="Whether poker_knightNG module is available")
    gpu_status: Optional[Dict[str, Any]] = Field(None, description="GPU server status and statistics")


class RequestTracking(BaseModel):
    """Model for tracking action requests"""
    request_id: str = Field(..., description="Unique request identifier")
    game_id: str = Field(..., description="Game ID")
    player_id: str = Field(..., description="Player ID")
    action: str = Field(..., description="Action type")
    amount: Optional[int] = Field(None, description="Bet amount if applicable")
    timestamp: float = Field(..., description="Unix timestamp")
    processed: bool = Field(..., description="Whether request was processed")
    duplicate: bool = Field(False, description="Whether this was a duplicate request")
    result: Optional[Dict[str, Any]] = Field(None, description="Result of processing")


class ChipMovement(BaseModel):
    """Model for tracking chip movements"""
    timestamp: float = Field(..., description="Unix timestamp")
    hand_number: int = Field(..., description="Hand number")
    player_id: str = Field(..., description="Player ID")
    player_name: str = Field(..., description="Player name")
    amount: int = Field(..., description="Amount moved (negative for bets, positive for wins)")
    reason: str = Field(..., description="Reason for movement")
    stack_before: int = Field(..., description="Stack before movement")
    stack_after: int = Field(..., description="Stack after movement")
    state_version: int = Field(..., description="Game state version")


class StateSnapshot(BaseModel):
    """Model for game state snapshots"""
    state_version: int = Field(..., description="State version number")
    timestamp: float = Field(..., description="Unix timestamp")
    phase: str = Field(..., description="Game phase")
    hand_number: int = Field(..., description="Current hand number")
    action_on: int = Field(..., description="Position of player to act")
    current_bet: int = Field(..., description="Current bet amount")
    board_cards: List[str] = Field(..., description="Community cards")
    player_states: List[Dict[str, Any]] = Field(..., description="Player state snapshots")
    pots: List[Dict[str, Any]] = Field(..., description="Pot information")
    chip_movements_count: int = Field(..., description="Number of chip movements recorded")
    validation_status: Dict[str, Any] = Field(..., description="State validation results")