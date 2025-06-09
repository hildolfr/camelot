"""
Wrapper around poker_knight module for Camelot application.
This module handles all poker calculations and validates inputs.
"""

from typing import List, Dict, Optional, Tuple
from poker_knight import solve_poker_hand
from .result_adapter import ResultAdapter


class PokerCalculator:
    """Handles poker hand calculations using the poker_knight module."""
    
    VALID_RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    VALID_SUITS = ['♠', '♥', '♦', '♣']
    
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
        simulation_mode: str = "default"
    ) -> Dict:
        """
        Calculate poker hand probabilities.
        
        Args:
            hero_hand: List of 2 cards for hero
            num_opponents: Number of opponents (1-6)
            board_cards: Optional list of 3-5 community cards
            simulation_mode: "fast", "default", or "precision"
        
        Returns:
            Dictionary with calculation results
        
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
        
        # Call poker_knight
        try:
            result = solve_poker_hand(
                hero_hand,
                num_opponents,
                board_cards,
                simulation_mode=simulation_mode
            )
            
            # Use ResultAdapter to normalize the result
            adapted_result = ResultAdapter.adapt_simulation_result(result)
            
            # Add request parameters to the response
            adapted_result.update({
                "hero_hand": hero_hand,
                "board_cards": board_cards or [],
                "num_opponents": num_opponents
            })
            
            return adapted_result
            
        except Exception as e:
            raise ValueError(f"Poker calculation failed: {str(e)}")