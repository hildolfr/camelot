"""AI Player implementation using poker_knightNG for advanced decision making."""

import random
from typing import Tuple, List, Optional, Dict, Any
import logging
import os
from datetime import datetime

from .poker_game import PlayerAction, GameState, Player, GamePhase

# Set up file-only logging for AI player
logger = logging.getLogger(__name__)
# Prevent propagation to root logger (no console output)
logger.propagate = False

# Use the same log directory as poker_game
current_file = os.path.abspath(__file__)
game_dir = os.path.dirname(current_file)
camelot_dir = os.path.dirname(game_dir)
src_dir = os.path.dirname(camelot_dir)
project_root = os.path.dirname(src_dir)
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Use the same rotating log file as poker_game
from logging.handlers import RotatingFileHandler
log_filename = os.path.join(log_dir, 'poker_game.log')
file_handler = RotatingFileHandler(
    log_filename,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,  # Keep 5 old files
    encoding='utf-8'
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)


class AIPlayer:
    """AI player that makes decisions using poker_knightNG calculations with advanced analysis."""
    
    def __init__(self, difficulty: str = "medium"):
        """Initialize AI player with difficulty level."""
        self.difficulty = difficulty
        
        # Decision parameters based on difficulty
        self.params = self._get_difficulty_params(difficulty)
    
    def _get_difficulty_params(self, difficulty: str) -> dict:
        """Get AI parameters based on difficulty level."""
        params = {
            "easy": {
                "bluff_frequency": 0.05,
                "fold_threshold": 0.25,
                "raise_threshold": 0.7,
                "call_threshold": 0.4,
                "aggression": 0.3,
                "tightness": 0.7,
                "randomness": 0.3
            },
            "medium": {
                "bluff_frequency": 0.15,
                "fold_threshold": 0.35,
                "raise_threshold": 0.6,
                "call_threshold": 0.45,
                "aggression": 0.5,
                "tightness": 0.5,
                "randomness": 0.2
            },
            "hard": {
                "bluff_frequency": 0.25,
                "fold_threshold": 0.4,
                "raise_threshold": 0.55,
                "call_threshold": 0.5,
                "aggression": 0.7,
                "tightness": 0.4,
                "randomness": 0.1
            },
            "expert": {
                "bluff_frequency": 0.3,
                "fold_threshold": 0.45,
                "raise_threshold": 0.5,
                "call_threshold": 0.5,
                "aggression": 0.8,
                "tightness": 0.3,
                "randomness": 0.05
            }
        }
        return params.get(difficulty, params["medium"])
    
    def decide_action(self, game_state: GameState, ai_player: Player) -> Tuple[PlayerAction, int]:
        """Decide what action to take based on game state."""
        # Add some randomness to make AI less predictable
        if random.random() < self.params["randomness"]:
            return self._random_action(game_state, ai_player)
        
        # Get pot odds
        pot_size = sum(pot.amount for pot in game_state.pots)
        to_call = game_state.current_bet - ai_player.current_bet
        pot_odds = to_call / (pot_size + to_call) if pot_size + to_call > 0 else 0
        
        # CRITICAL: Ensure to_call is never negative
        if to_call < 0:
            logger.error(f"CRITICAL ERROR: to_call is negative! current_bet={game_state.current_bet}, ai_bet={ai_player.current_bet}")
            to_call = 0
        
        # Check if facing an all-in situation
        is_facing_all_in = self._is_facing_all_in(game_state)
        can_only_call_all_in = to_call >= ai_player.stack
        
        # Log all-in situations
        if is_facing_all_in or can_only_call_all_in:
            logger.info(f"AI {ai_player.id} facing all-in: to_call={to_call}, stack={ai_player.stack}")
            logger.info(f"Current bet: {game_state.current_bet}, AI's current bet: {ai_player.current_bet}")
            logger.info(f"Is someone all-in: {is_facing_all_in}, Must go all-in to call: {can_only_call_all_in}")
        
        # Get advanced analysis from poker_knightNG if available
        analysis = self._get_poker_analysis(game_state, ai_player)
        
        # Use advanced metrics if available, otherwise fall back to simple logic
        if analysis and 'win_probability' in analysis:
            action, amount = self._make_advanced_decision(game_state, ai_player, analysis)
        else:
            # Fall back to simple logic
            if game_state.phase == GamePhase.PRE_FLOP:
                action, amount = self._preflop_decision(game_state, ai_player, pot_odds)
            else:
                action, amount = self._postflop_decision(game_state, ai_player, pot_odds)
        
        # Final validation: NEVER allow CHECK when facing a bet
        if action == PlayerAction.CHECK and game_state.current_bet > ai_player.current_bet:
            logger.error(f"CRITICAL: AI tried to CHECK when facing bet! Changing to CALL")
            logger.error(f"State: current_bet={game_state.current_bet}, ai_bet={ai_player.current_bet}")
            action = PlayerAction.CALL
        
        # Final validation: If CALL would require all chips, must use ALL_IN
        if action == PlayerAction.CALL and to_call >= ai_player.stack:
            logger.info(f"Converting CALL to ALL_IN since to_call ({to_call}) >= stack ({ai_player.stack})")
            action = PlayerAction.ALL_IN
        
        logger.info(f"AI {ai_player.id} final decision: {action.value} (amount: {amount})")
        return action, amount
    
    def _preflop_decision(self, game_state: GameState, ai_player: Player, pot_odds: float) -> Tuple[PlayerAction, int]:
        """Make pre-flop decision."""
        to_call = game_state.current_bet - ai_player.current_bet
        
        # Debug logging
        logger.info(f"\n=== AI {ai_player.id} PRE-FLOP DECISION ===")
        logger.info(f"Game current_bet: {game_state.current_bet}")
        logger.info(f"AI current_bet: {ai_player.current_bet}")
        logger.info(f"To call: {to_call}")
        logger.info(f"AI stack: {ai_player.stack}")
        
        # Position-based play
        is_late_position = ai_player.position >= len(game_state.players) - 2
        
        # Simplified hand strength estimation (would use poker_knight in real implementation)
        hand_strength = self._estimate_preflop_strength(ai_player.hole_cards)
        
        # Adjust for position
        if is_late_position:
            hand_strength *= 1.2
        
        # Decision logic
        if to_call == 0:  # No bet to call
            # Double-check that we really can check
            if game_state.current_bet > ai_player.current_bet:
                logger.error(f"ERROR: AI thinks to_call=0 but current_bet ({game_state.current_bet}) > ai_current_bet ({ai_player.current_bet})")
                logger.error("Forcing CALL instead of CHECK to avoid invalid action")
                return PlayerAction.CALL, 0
            
            if hand_strength > self.params["raise_threshold"]:
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:  # Can make a valid raise
                    return PlayerAction.RAISE, raise_amount
                else:
                    return PlayerAction.CHECK, 0
            elif random.random() < self.params["bluff_frequency"]:
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:  # Can make a valid raise
                    return PlayerAction.RAISE, raise_amount
                else:
                    return PlayerAction.CHECK, 0
            else:
                return PlayerAction.CHECK, 0
        else:  # Facing a bet
            # Check if we're facing an all-in or if calling would put us all-in
            if to_call >= ai_player.stack:
                # Can only go all-in or fold
                if hand_strength > self.params["call_threshold"] * 1.2:  # Need stronger hand for all-in
                    logger.info(f"AI {ai_player.id} calling all-in with hand_strength={hand_strength}")
                    return PlayerAction.ALL_IN, 0
                else:
                    logger.info(f"AI {ai_player.id} folding to all-in with hand_strength={hand_strength}")
                    return PlayerAction.FOLD, 0
            
            # Normal betting logic
            if hand_strength < self.params["fold_threshold"]:
                return PlayerAction.FOLD, 0
            elif hand_strength > self.params["raise_threshold"] and ai_player.stack > to_call * 3:
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:  # Can make a valid raise
                    return PlayerAction.RAISE, raise_amount
                else:  # Can't raise enough, just call
                    logger.info(f"AI {ai_player.id} wanted to raise but can't meet minimum, calling instead")
                    return PlayerAction.CALL, 0
            elif hand_strength > self.params["call_threshold"] or pot_odds < hand_strength:
                return PlayerAction.CALL, 0
            else:
                return PlayerAction.FOLD, 0
    
    def _postflop_decision(self, game_state: GameState, ai_player: Player, pot_odds: float) -> Tuple[PlayerAction, int]:
        """Make post-flop decision."""
        to_call = game_state.current_bet - ai_player.current_bet
        
        # Debug logging
        logger.info(f"\n=== AI {ai_player.id} POST-FLOP DECISION ===")
        logger.info(f"Phase: {game_state.phase.name}")
        logger.info(f"Game current_bet: {game_state.current_bet}")
        logger.info(f"AI current_bet: {ai_player.current_bet}")
        logger.info(f"To call: {to_call}")
        logger.info(f"AI stack: {ai_player.stack}")
        
        # Simplified hand strength (would use poker_knight in real implementation)
        hand_strength = self._estimate_postflop_strength(ai_player.hole_cards, game_state.board_cards)
        
        # Decision logic
        if to_call == 0:  # No bet to call
            # Double-check that we really can check
            if game_state.current_bet > ai_player.current_bet:
                logger.error(f"ERROR: AI thinks to_call=0 but current_bet ({game_state.current_bet}) > ai_current_bet ({ai_player.current_bet})")
                logger.error("Forcing CALL instead of CHECK to avoid invalid action")
                return PlayerAction.CALL, 0
            
            if hand_strength > self.params["raise_threshold"]:
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                return PlayerAction.RAISE, raise_amount
            elif random.random() < self.params["bluff_frequency"] * 0.7:  # Less bluffing post-flop
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                return PlayerAction.RAISE, raise_amount
            else:
                return PlayerAction.CHECK, 0
        else:  # Facing a bet
            # Check if we're facing an all-in or if calling would put us all-in
            if to_call >= ai_player.stack:
                # Can only go all-in or fold
                if hand_strength > self.params["call_threshold"]:  # Slightly looser post-flop for all-in
                    logger.info(f"AI {ai_player.id} calling all-in post-flop with hand_strength={hand_strength}")
                    return PlayerAction.ALL_IN, 0
                else:
                    logger.info(f"AI {ai_player.id} folding to all-in post-flop with hand_strength={hand_strength}")
                    return PlayerAction.FOLD, 0
            
            # Normal betting logic
            if hand_strength < self.params["fold_threshold"] * 0.8:  # Tighter post-flop
                return PlayerAction.FOLD, 0
            elif hand_strength > self.params["raise_threshold"] and ai_player.stack > to_call * 3:
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:  # Can make a valid raise
                    return PlayerAction.RAISE, raise_amount
                else:  # Can't raise enough, just call
                    logger.info(f"AI {ai_player.id} wanted to raise but can't meet minimum, calling instead")
                    return PlayerAction.CALL, 0
            elif hand_strength > self.params["call_threshold"] or pot_odds < hand_strength:
                return PlayerAction.CALL, 0
            else:
                return PlayerAction.FOLD, 0
    
    def _random_action(self, game_state: GameState, ai_player: Player) -> Tuple[PlayerAction, int]:
        """Make a random but legal action."""
        to_call = game_state.current_bet - ai_player.current_bet
        
        if to_call == 0:
            # Can check or raise
            if random.random() < 0.7:
                return PlayerAction.CHECK, 0
            else:
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:  # Can make a valid raise
                    return PlayerAction.RAISE, raise_amount
                else:
                    return PlayerAction.CHECK, 0
        else:
            # Must call, raise, or fold
            # Check if calling would put us all-in
            if to_call >= ai_player.stack:
                # Can only go all-in or fold
                if random.random() < 0.6:  # 60% chance to call all-in randomly
                    return PlayerAction.ALL_IN, 0
                else:
                    return PlayerAction.FOLD, 0
            
            # Normal random logic
            rand = random.random()
            if rand < 0.2:
                return PlayerAction.FOLD, 0
            elif rand < 0.7:
                return PlayerAction.CALL, 0
            else:
                if ai_player.stack > to_call * 2:
                    raise_amount = self._calculate_raise_amount(game_state, ai_player)
                    if raise_amount > 0:  # Can make a valid raise
                        return PlayerAction.RAISE, raise_amount
                    else:
                        return PlayerAction.CALL, 0
                else:
                    return PlayerAction.CALL, 0
    
    def _calculate_raise_amount(self, game_state: GameState, ai_player: Player) -> int:
        """Calculate raise amount based on aggression and pot size."""
        pot_size = sum(pot.amount for pot in game_state.pots)
        # Add current bets to pot size for more accurate calculation
        for p in game_state.players:
            pot_size += p.current_bet
        
        min_raise = game_state.min_raise
        # Calculate how much we need to put in total to make a valid raise
        to_call = game_state.current_bet - ai_player.current_bet
        max_raise = ai_player.stack - to_call  # Max we can raise beyond current bet
        
        # Log raise calculation
        logger.info(f"AI raise calculation: min_raise={min_raise}, to_call={to_call}, max_raise={max_raise}")
        logger.info(f"Current bet: {game_state.current_bet}, AI's bet: {ai_player.current_bet}, AI stack: {ai_player.stack}")
        
        # If we can't make minimum raise, we can't raise at all
        if max_raise < min_raise:
            logger.info(f"Cannot make minimum raise: max_raise ({max_raise}) < min_raise ({min_raise})")
            return 0  # Signal that we can't raise
        
        # Base raise on pot size and aggression
        base_raise = int(pot_size * (0.5 + self.params["aggression"] * 0.5))
        
        # Ensure within limits - raise amount is ABOVE current bet
        raise_amount = max(min_raise, min(base_raise, max_raise))
        
        # Sometimes go all-in with strong hands
        if random.random() < self.params["aggression"] * 0.1:
            raise_amount = max_raise
        
        logger.info(f"AI calculated raise amount: {raise_amount} (will raise to {game_state.current_bet + raise_amount})")
        return raise_amount
    
    def _is_facing_all_in(self, game_state: GameState) -> bool:
        """Check if any player has gone all-in."""
        for player in game_state.players:
            if not player.has_folded and player.stack == 0 and player.current_bet > 0:
                return True
        return False
    
    def _estimate_preflop_strength(self, hole_cards: List[str]) -> float:
        """Estimate pre-flop hand strength (simplified)."""
        if len(hole_cards) != 2:
            return 0.5
        
        # Extract ranks
        ranks = []
        for card in hole_cards:
            if card.startswith('10'):
                ranks.append('10')
            else:
                ranks.append(card[0])
        
        # High card values
        rank_values = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, '10': 10,
                      '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
        
        values = [rank_values.get(r, 2) for r in ranks]
        
        # Pocket pairs
        if values[0] == values[1]:
            return 0.85 + (values[0] / 14) * 0.15
        
        # High cards
        high_card_strength = (sum(values) / 28) * 0.7
        
        # Suited bonus
        suited = hole_cards[0][-1] == hole_cards[1][-1]
        if suited:
            high_card_strength += 0.1
        
        # Connected bonus
        if abs(values[0] - values[1]) == 1:
            high_card_strength += 0.05
        
        return min(1.0, high_card_strength)
    
    def _estimate_postflop_strength(self, hole_cards: List[str], board_cards: List[str]) -> float:
        """Estimate post-flop hand strength (simplified)."""
        # In real implementation, would use poker_knight to evaluate
        # For now, return random strength weighted by board texture
        
        all_cards = hole_cards + board_cards
        
        # Count suits for flush possibilities
        suits = {}
        for card in all_cards:
            suit = card[-1]
            suits[suit] = suits.get(suit, 0) + 1
        
        # Flush draw or made flush
        max_suit = max(suits.values()) if suits else 0
        if max_suit >= 5:
            return 0.9
        elif max_suit == 4:
            return 0.6
        
        # Simple estimation
        base_strength = self._estimate_preflop_strength(hole_cards)
        
        # Adjust based on board texture (simplified)
        return base_strength * (0.7 + random.random() * 0.3)
    
    def _get_poker_analysis(self, game_state: GameState, ai_player: Player) -> Optional[Dict[str, Any]]:
        """Get advanced analysis from poker_knightNG."""
        try:
            # Import here to avoid circular imports
            from ..core.cache_init import get_cached_calculator
            calculator = get_cached_calculator()
            
            # Determine street
            street_map = {
                GamePhase.PRE_FLOP: "preflop",
                GamePhase.FLOP: "flop",
                GamePhase.TURN: "turn",
                GamePhase.RIVER: "river"
            }
            street = street_map.get(game_state.phase, "preflop")
            
            # Determine action facing
            to_call = game_state.current_bet - ai_player.current_bet
            if to_call > 0:
                action_to_hero = "bet" if game_state.current_bet == game_state.big_blind else "raise"
            else:
                action_to_hero = "check"
            
            # Calculate bet size relative to pot
            pot_size = sum(pot.amount for pot in game_state.pots)
            bet_size = to_call / pot_size if pot_size > 0 and to_call > 0 else 0
            
            # Count active players
            active_players = [p for p in game_state.players if not p.has_folded]
            num_opponents = len(active_players) - 1
            
            # Get stack sizes
            stack_sizes = [p.stack + p.current_bet for p in active_players if p.id == ai_player.id or not p.has_folded]
            
            # Players to act
            players_to_act = sum(1 for p in game_state.players[game_state.current_player_index + 1:] if not p.has_folded)
            
            # Call calculator with all new parameters
            result = calculator.calculate(
                hero_hand=ai_player.hole_cards,
                num_opponents=num_opponents,
                board_cards=game_state.board_cards if game_state.board_cards else None,
                simulation_mode="fast",  # Fast mode for game play
                action_to_hero=action_to_hero,
                bet_size=bet_size,
                street=street,
                pot_size=pot_size,
                stack_sizes=stack_sizes,
                players_to_act=players_to_act
            )
            
            return result
            
        except Exception as e:
            logger.debug(f"Could not get poker analysis: {e}")
            return None
    
    def _make_advanced_decision(self, game_state: GameState, ai_player: Player, analysis: Dict[str, Any]) -> Tuple[PlayerAction, int]:
        """Make decision based on advanced poker_knightNG analysis."""
        to_call = game_state.current_bet - ai_player.current_bet
        
        # Extract key metrics
        win_prob = analysis.get('win_probability', 0.5)
        pot_odds = analysis.get('pot_odds', 0)
        equity_needed = analysis.get('equity_needed', pot_odds)
        mdf = analysis.get('mdf', 0.5)  # Minimum defense frequency
        spr = analysis.get('spr', 10)  # Stack-to-pot ratio
        commitment_threshold = analysis.get('commitment_threshold', 4)
        
        logger.info(f"\n=== AI {ai_player.id} ADVANCED DECISION ===")
        logger.info(f"Win probability: {win_prob:.2%}, Pot odds: {pot_odds:.2%}")
        logger.info(f"Equity needed: {equity_needed:.2%}, MDF: {mdf:.2%}")
        logger.info(f"SPR: {spr:.2f}, Commitment threshold: {commitment_threshold:.2f}")
        
        # Adjust for difficulty
        adjusted_win_prob = win_prob * (1 - self.params["randomness"] * 0.3)
        
        # Decision logic based on advanced metrics
        if to_call == 0:  # No bet to face
            if win_prob > 0.7:  # Strong hand
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:
                    return PlayerAction.RAISE, raise_amount
            elif win_prob > 0.5 and random.random() < self.params["aggression"]:
                # Semi-bluff with decent equity
                raise_amount = self._calculate_raise_amount(game_state, ai_player)
                if raise_amount > 0:
                    return PlayerAction.RAISE, raise_amount
            return PlayerAction.CHECK, 0
            
        else:  # Facing a bet
            # Check if we're pot committed
            if spr <= commitment_threshold and win_prob > 0.3:
                logger.info(f"AI {ai_player.id} is pot committed (SPR={spr:.2f})")
                if to_call >= ai_player.stack:
                    return PlayerAction.ALL_IN, 0
                else:
                    return PlayerAction.CALL, 0
            
            # Use MDF for defense decisions
            defense_roll = random.random()
            should_defend = defense_roll < mdf
            
            # Check if we have direct odds to call
            if adjusted_win_prob > equity_needed:
                # We have the odds
                if to_call >= ai_player.stack:
                    return PlayerAction.ALL_IN, 0
                elif win_prob > 0.65 and ai_player.stack > to_call * 2:
                    # Strong hand, consider raising
                    raise_amount = self._calculate_raise_amount(game_state, ai_player)
                    if raise_amount > 0:
                        return PlayerAction.RAISE, raise_amount
                return PlayerAction.CALL, 0
            
            # Bluff catching based on MDF
            elif should_defend and win_prob > 0.35:
                logger.info(f"AI {ai_player.id} defending based on MDF")
                if to_call >= ai_player.stack:
                    # Only defend with reasonable equity when all-in
                    if win_prob > 0.4:
                        return PlayerAction.ALL_IN, 0
                    else:
                        return PlayerAction.FOLD, 0
                return PlayerAction.CALL, 0
            
            # Fold
            else:
                return PlayerAction.FOLD, 0