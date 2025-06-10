"""
Cache key generator for consistent cache key creation.
"""

from typing import List, Optional


class CacheKeyGenerator:
    """Generates consistent cache keys for poker calculations."""
    
    @staticmethod
    def generate_key(hero_hand: List[str], 
                    num_opponents: int,
                    board_cards: Optional[List[str]], 
                    simulation_mode: str) -> str:
        """
        Generate a cache key from game parameters.
        
        Format: "hero_hand|num_opponents|board_cards|mode"
        Example: "A♠K♥|2|Q♦J♣10♠|default"
        
        Args:
            hero_hand: List of 2 cards for hero
            num_opponents: Number of opponents (1-6)
            board_cards: Optional list of 3-5 community cards
            simulation_mode: "fast", "default", or "precision"
            
        Returns:
            Cache key string
        """
        # Join hero hand (no sorting to preserve exact permutation)
        hero_str = "".join(hero_hand)
        
        # Join board cards (sorted for consistency)
        board_str = ""
        if board_cards:
            # Sort board cards to ensure consistent keys
            # e.g., [Q♦, J♣, 10♠] and [J♣, Q♦, 10♠] should have same key
            sorted_board = sorted(board_cards)
            board_str = "".join(sorted_board)
        
        # Build cache key
        key = f"{hero_str}|{num_opponents}|{board_str}|{simulation_mode}"
        
        return key
    
    @staticmethod
    def parse_key(cache_key: str) -> dict:
        """
        Parse a cache key back into components.
        
        Args:
            cache_key: Cache key string
            
        Returns:
            Dictionary with parsed components
        """
        parts = cache_key.split('|')
        if len(parts) != 4:
            raise ValueError(f"Invalid cache key format: {cache_key}")
        
        hero_str, num_opponents_str, board_str, simulation_mode = parts
        
        # Parse hero hand (always 2 cards)
        hero_hand = []
        if len(hero_str) >= 4:  # At least 2 cards with suits
            # Handle 10 as special case
            if hero_str.startswith('10'):
                hero_hand.append(hero_str[:3])  # 10X
                hero_hand.append(hero_str[3:])   # Remaining card
            elif len(hero_str) >= 5 and '10' in hero_str[2:]:
                # Second card might be 10
                hero_hand.append(hero_str[:2])   # First card
                hero_hand.append(hero_str[2:])   # 10X
            else:
                # Normal case: both cards are single character ranks
                hero_hand.append(hero_str[:2])   # First card
                hero_hand.append(hero_str[2:])   # Second card
        
        # Parse board cards
        board_cards = []
        if board_str:
            # Parse board cards (3-5 cards)
            i = 0
            while i < len(board_str):
                if i + 2 < len(board_str) and board_str[i:i+2] == '10':
                    board_cards.append(board_str[i:i+3])
                    i += 3
                else:
                    board_cards.append(board_str[i:i+2])
                    i += 2
        
        return {
            'hero_hand': hero_hand,
            'num_opponents': int(num_opponents_str),
            'board_cards': board_cards,
            'simulation_mode': simulation_mode
        }
    
    @staticmethod
    def create_metadata(hero_hand: List[str], 
                       num_opponents: int,
                       board_cards: Optional[List[str]], 
                       simulation_mode: str) -> dict:
        """
        Create metadata dictionary for database storage.
        
        Args:
            hero_hand: List of 2 cards for hero
            num_opponents: Number of opponents
            board_cards: Optional list of community cards
            simulation_mode: Simulation mode
            
        Returns:
            Metadata dictionary
        """
        return {
            'hero_hand': "".join(hero_hand),
            'num_opponents': num_opponents,
            'board_cards': "".join(board_cards) if board_cards else "",
            'simulation_mode': simulation_mode
        }