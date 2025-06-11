"""Dealer implementation for managing game flow."""

import logging
from typing import List, Dict, Any, Optional

from .poker_game import GameState, Player

logger = logging.getLogger(__name__)
# Prevent propagation to root logger (no console output)
logger.propagate = False


class Dealer:
    """Manages game flow and enforces rules."""
    
    def __init__(self):
        """Initialize the dealer."""
        pass
    
    def evaluate_hand(self, hole_cards: List[str], board_cards: List[str]) -> Dict[str, Any]:
        """
        Evaluate a poker hand.
        
        In a real implementation, this would use poker_knight.
        For now, returns a placeholder.
        """
        # This is where we would integrate with poker_knight
        # to get actual hand evaluation
        
        return {
            "rank": 1000,  # Placeholder rank
            "hand_type": "high_card",
            "description": "High Card"
        }
    
    def determine_winners(self, players: List[Player], board_cards: List[str]) -> List[Dict[str, Any]]:
        """
        Determine the winners of a hand.
        
        Returns list of winner info with pot distribution.
        """
        active_players = [p for p in players if not p.has_folded]
        
        if len(active_players) == 1:
            # Only one player left, they win
            return [{
                "player_id": active_players[0].id,
                "amount": sum(p.total_bet_this_round for p in players),
                "hand_description": "Last player standing"
            }]
        
        # Evaluate all hands
        player_hands = []
        for player in active_players:
            hand_eval = self.evaluate_hand(player.hole_cards, board_cards)
            player_hands.append({
                "player": player,
                "evaluation": hand_eval
            })
        
        # Sort by hand rank (higher is better)
        player_hands.sort(key=lambda x: x["evaluation"]["rank"], reverse=True)
        
        # Find all winners (could be ties)
        winners = []
        best_rank = player_hands[0]["evaluation"]["rank"]
        
        for ph in player_hands:
            if ph["evaluation"]["rank"] == best_rank:
                winners.append(ph)
            else:
                break
        
        # Calculate pot distribution
        total_pot = sum(p.total_bet_this_round for p in players)
        pot_per_winner = total_pot // len(winners)
        
        winner_info = []
        for w in winners:
            winner_info.append({
                "player_id": w["player"].id,
                "amount": pot_per_winner,
                "hand_description": w["evaluation"]["description"]
            })
        
        # Handle remainder
        if total_pot % len(winners) > 0:
            winner_info[0]["amount"] += total_pot % len(winners)
        
        return winner_info
    
    def create_side_pots(self, players: List[Player]) -> List[Dict[str, Any]]:
        """
        Create side pots for all-in situations.
        
        Returns list of pots with eligible players.
        """
        # Get all unique bet amounts
        bet_amounts = sorted(set(p.total_bet_this_round for p in players if p.total_bet_this_round > 0))
        
        if not bet_amounts:
            return []
        
        pots = []
        remaining_players = [p for p in players if not p.has_folded]
        
        previous_amount = 0
        for bet_amount in bet_amounts:
            # Players eligible for this pot level
            eligible_players = [p for p in remaining_players 
                              if p.total_bet_this_round >= bet_amount]
            
            if eligible_players:
                pot_amount = (bet_amount - previous_amount) * len(eligible_players)
                pots.append({
                    "amount": pot_amount,
                    "eligible_players": [p.id for p in eligible_players]
                })
            
            # Remove all-in players who can't contest higher pots
            remaining_players = [p for p in remaining_players 
                               if p.stack > 0 or p.total_bet_this_round > bet_amount]
            
            previous_amount = bet_amount
        
        return pots