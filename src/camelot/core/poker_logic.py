"""
Wrapper around poker_knight module for Camelot application.
This module handles all poker calculations and validates inputs.
"""

from typing import List, Dict, Optional, Tuple, Any
from .poker_server import get_poker_server
from .result_adapter import ResultAdapter

# Note: poker_knightNG provides GPU keep-alive for performance
# Camelot maintains its own caching layer for long-term persistence
import os
import logging

cache_dir = os.path.expanduser("~/.camelot_cache")
os.makedirs(cache_dir, exist_ok=True)

logger = logging.getLogger(__name__)


class PokerCalculator:
    """Handles poker hand calculations using the poker_knightNG module."""
    
    VALID_RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    VALID_SUITS = ['♠', '♥', '♦', '♣']
    
    # Rank conversion for poker_knightNG (uses 'T' for Ten)
    RANK_CONVERSION = {'10': 'T'}
    
    def __init__(self):
        """Initialize the calculator with poker_knightNG server."""
        # Get the singleton server instance
        self._server = get_poker_server()
        
        # Create a dedicated thread pool for user requests
        # This ensures cache warming doesn't block user calculations
        from concurrent.futures import ThreadPoolExecutor
        self._user_executor = ThreadPoolExecutor(
            max_workers=4,  # Dedicated threads for user requests
            thread_name_prefix="user_calc"
        )
    
    @staticmethod
    def validate_card(card: str) -> bool:
        """Validate a single card string."""
        if not card or len(card) < 2:
            return False
        
        # Handle 10 as a special case
        if card.startswith('10'):
            rank = '10'
            suit = card[2:]
        else:
            rank = card[0]
            suit = card[1:]
        
        return rank in PokerCalculator.VALID_RANKS and suit in PokerCalculator.VALID_SUITS
    
    @staticmethod
    def convert_card_format(card: str) -> str:
        """
        Convert our card format to poker_knightNG format.
        Mainly handles '10' -> 'T' conversion.
        poker_knightNG accepts unicode suits directly.
        """
        if card.startswith('10'):
            return 'T' + card[2:]
        return card
    
    @staticmethod
    def validate_hand(cards: List[str], board_cards: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Validate a poker hand and board cards.
        Returns (is_valid, error_message)
        """
        all_cards = cards.copy()
        if board_cards:
            all_cards.extend(board_cards)
        
        # Check for valid card format
        for card in all_cards:
            if not PokerCalculator.validate_card(card):
                return False, f"Invalid card format: {card}"
        
        # Check for duplicates
        if len(all_cards) != len(set(all_cards)):
            return False, "Duplicate cards detected"
        
        # Check hand size
        if len(cards) != 2:
            return False, "Hero hand must contain exactly 2 cards"
        
        # Check board size
        if board_cards and len(board_cards) not in [3, 4, 5]:
            return False, "Board must contain 3, 4, or 5 cards"
        
        return True, ""
    
    def calculate(
        self,
        hero_hand: List[str],
        num_opponents: int,
        board_cards: Optional[List[str]] = None,
        simulation_mode: str = "default",
        hero_position: Optional[str] = None,
        stack_sizes: Optional[List[int]] = None,
        pot_size: Optional[int] = None,
        tournament_context: Optional[Dict[str, Any]] = None,
        action_to_hero: Optional[str] = None,
        bet_size: Optional[float] = None,
        street: Optional[str] = None,
        players_to_act: Optional[int] = None,
        tournament_stage: Optional[str] = None,
        blind_level: Optional[int] = None
    ) -> Dict:
        """
        Calculate poker hand probabilities using poker_knightNG server.
        
        Args:
            hero_hand: List of 2 cards for hero
            num_opponents: Number of opponents (1-6)
            board_cards: Optional list of 3-5 community cards
            simulation_mode: "fast", "default", or "precision"
            hero_position: Position at table ("early", "middle", "late", "button", "sb", "bb")
            stack_sizes: Stack sizes for all players
            pot_size: Current pot size
            tournament_context: Tournament info for ICM calculations
            action_to_hero: Current action facing hero ("check", "bet", "raise", "reraise")
            bet_size: Current bet size relative to pot
            street: Current street ("preflop", "flop", "turn", "river")
            players_to_act: Number of players still to act after hero
            tournament_stage: Tournament stage ("early", "middle", "bubble", "final_table")
            blind_level: Current blind level for tournament pressure
        
        Returns:
            Dictionary with calculation results including advanced analysis
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        is_valid, error_msg = self.validate_hand(hero_hand, board_cards)
        if not is_valid:
            raise ValueError(error_msg)
        
        if not 1 <= num_opponents <= 6:
            raise ValueError("Number of opponents must be between 1 and 6")
        
        if simulation_mode not in ["fast", "default", "precision"]:
            raise ValueError("Simulation mode must be 'fast', 'default', or 'precision'")
        
        # Build kwargs for all parameters
        kwargs = {
            'simulation_mode': simulation_mode
        }
        
        # Add all optional parameters if provided
        if hero_position:
            kwargs['hero_position'] = hero_position
        if stack_sizes:
            kwargs['stack_sizes'] = stack_sizes
        if pot_size is not None:
            kwargs['pot_size'] = pot_size
        if tournament_context:
            kwargs['tournament_context'] = tournament_context
        if action_to_hero:
            kwargs['action_to_hero'] = action_to_hero
        if bet_size is not None:
            kwargs['bet_size'] = bet_size
        if street:
            kwargs['street'] = street
        if players_to_act is not None:
            kwargs['players_to_act'] = players_to_act
        if tournament_stage:
            kwargs['tournament_stage'] = tournament_stage
        if blind_level is not None:
            kwargs['blind_level'] = blind_level
        
        # Use server API for calculation
        try:
            # Log if this is a cold start (but still perform calculation)
            if self._server.is_cold_start():
                logger.info("Performing cold start calculation (metrics will be excluded)")
            
            # Convert card format for poker_knightNG
            converted_hero_hand = [self.convert_card_format(card) for card in hero_hand]
            converted_board_cards = None
            if board_cards:
                converted_board_cards = [self.convert_card_format(card) for card in board_cards]
            
            result = self._server.solve(
                converted_hero_hand,
                num_opponents,
                converted_board_cards,
                **kwargs
            )
            
            # Use ResultAdapter to normalize the result
            adapted_result = ResultAdapter.adapt_simulation_result(result)
            
            # Add request parameters to the response
            adapted_result.update({
                "hero_hand": hero_hand,
                "board_cards": board_cards or [],
                "num_opponents": num_opponents
            })
            
            # Add cold/warm indicator (for metrics filtering)
            adapted_result["_is_cold_start"] = getattr(result, '_is_cold_start', False)
            
            return adapted_result
            
        except Exception as e:
            logger.error(f"Poker calculation failed: {e}")
            raise ValueError(f"Poker calculation failed: {str(e)}")
    
    def calculate_batch(self, problems: List[Dict[str, Any]]) -> List[Optional[Dict]]:
        """
        Calculate multiple poker problems in batch for efficiency.
        
        Args:
            problems: List of problem dictionaries with calculation parameters
        
        Returns:
            List of result dictionaries (None for invalid inputs)
        """
        try:
            # Log if this is a cold start
            if self._server.is_cold_start():
                logger.info(f"Performing cold start batch calculation ({len(problems)} problems)")
            
            # Convert card formats in all problems
            converted_problems = []
            for problem in problems:
                converted_problem = problem.copy()
                
                # Convert hero_hand
                if 'hero_hand' in converted_problem:
                    converted_problem['hero_hand'] = [
                        self.convert_card_format(card) for card in converted_problem['hero_hand']
                    ]
                
                # Convert board_cards if present
                if 'board_cards' in converted_problem and converted_problem['board_cards']:
                    converted_problem['board_cards'] = [
                        self.convert_card_format(card) for card in converted_problem['board_cards']
                    ]
                
                converted_problems.append(converted_problem)
            
            # Use server batch API
            results = self._server.solve_batch(converted_problems)
            
            # Adapt all results
            adapted_results = []
            for i, result in enumerate(results):
                if result is None:
                    adapted_results.append(None)
                else:
                    # Adapt the result
                    adapted = ResultAdapter.adapt_simulation_result(result)
                    
                    # Add request parameters from original problem
                    problem = problems[i]
                    adapted.update({
                        "hero_hand": problem.get("hero_hand", []),
                        "board_cards": problem.get("board_cards", []),
                        "num_opponents": problem.get("num_opponents", 0)
                    })
                    
                    # Add cold/warm indicator
                    adapted["_is_cold_start"] = getattr(result, '_is_cold_start', False)
                    
                    adapted_results.append(adapted)
            
            return adapted_results
            
        except Exception as e:
            logger.error(f"Batch calculation failed: {e}")
            raise ValueError(f"Batch calculation failed: {str(e)}")
    
    def get_server_statistics(self) -> Dict[str, Any]:
        """Get statistics from the poker server."""
        return self._server.get_statistics()
    
    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the poker server."""
        return self._server.health_check()