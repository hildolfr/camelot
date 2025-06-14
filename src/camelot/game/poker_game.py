"""Texas Hold'em Game Engine with animations and visual effects"""

import random
import time
import json
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum, auto
from dataclasses import dataclass, field
import asyncio
import logging
import os
from datetime import datetime

from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from ..core.hand_evaluator import evaluate_hand, get_winning_players, HandEvaluation

# Set up file-only logging for poker game
logger = logging.getLogger(__name__)
# Prevent propagation to root logger (no console output)
logger.propagate = False

# Create logs directory if it doesn't exist
# Go up to camelot root directory
current_file = os.path.abspath(__file__)
game_dir = os.path.dirname(current_file)  # .../game/
camelot_dir = os.path.dirname(game_dir)  # .../camelot/
src_dir = os.path.dirname(camelot_dir)  # .../src/
project_root = os.path.dirname(src_dir)  # .../camelot/
log_dir = os.path.join(project_root, 'logs')
os.makedirs(log_dir, exist_ok=True)

# Use rotating file handler - max 10MB per file, keep 5 backup files
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

# Also add a daily rotating handler for bug reports specifically
bug_report_filename = os.path.join(log_dir, 'bug_reports.log')
bug_handler = TimedRotatingFileHandler(
    bug_report_filename,
    when='midnight',  # Rotate daily
    interval=1,
    backupCount=30,  # Keep 30 days of bug reports
    encoding='utf-8'
)
bug_handler.setLevel(logging.ERROR)  # Only ERROR level (bug reports)
bug_handler.setFormatter(file_formatter)
logger.addHandler(bug_handler)

logger.info(f"\n{'='*80}\nNEW POKER GAME SESSION STARTED\nLog file: {log_filename}\n{'='*80}")


class GamePhase(Enum):
    """Game phases for Texas Hold'em"""
    WAITING = auto()
    PRE_FLOP = auto()
    FLOP = auto()
    TURN = auto()
    RIVER = auto()
    SHOWDOWN = auto()
    GAME_OVER = auto()


class PlayerAction(Enum):
    """Possible player actions"""
    CHECK = "check"
    CALL = "call"
    RAISE = "raise"
    FOLD = "fold"
    ALL_IN = "all_in"


@dataclass
class Player:
    """Player in the game"""
    id: str
    name: str
    stack: int
    position: int
    is_ai: bool = True
    is_active: bool = True
    has_folded: bool = False
    hole_cards: List[str] = field(default_factory=list)
    current_bet: int = 0
    total_bet_this_hand: int = 0  # Total amount bet in this entire hand
    last_action: Optional[PlayerAction] = None
    
    def reset_for_new_hand(self):
        """Reset player state for new hand"""
        self.hole_cards = []
        self.current_bet = 0
        self.total_bet_this_hand = 0
        self.has_folded = False
        self.last_action = None
        self.is_active = self.stack > 0
        
        # Clear hand history attributes
        if hasattr(self, '_won_amount'):
            delattr(self, '_won_amount')
        if hasattr(self, '_winning_hand'):
            delattr(self, '_winning_hand')


@dataclass
class Pot:
    """Represents a pot (main or side)"""
    amount: int
    eligible_players: List[str]  # Player IDs


@dataclass
class GameState:
    """Complete game state"""
    game_id: str
    phase: GamePhase
    players: List[Player]
    board_cards: List[str]
    deck: List[str]
    pots: List[Pot]
    current_bet: int
    min_raise: int
    dealer_position: int
    action_on: int  # Position of player to act
    big_blind: int
    small_blind: int
    hand_number: int
    
    # Animation and visual state
    last_action_info: Dict[str, Any] = field(default_factory=dict)
    pending_animations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Turn-based card dealing
    awaiting_card_deal: bool = False
    all_players_all_in: bool = False
    cards_dealt_for_phase: Dict[GamePhase, bool] = field(default_factory=dict)
    
    def get_active_players(self) -> List[Player]:
        """Get all active (not folded) players who can still act"""
        # Note: This should only be used for determining who CAN act
        # For betting round completion, use get_players_in_hand() instead
        return [p for p in self.players if not p.has_folded and p.stack > 0]
    
    def get_players_in_hand(self) -> List[Player]:
        """Get all players still in the hand (not folded)"""
        return [p for p in self.players if not p.has_folded]
    
    def get_next_active_position(self, position: int) -> int:
        """Get next active player position"""
        n = len(self.players)
        for i in range(1, n + 1):  # Check all players including looping back
            next_pos = (position + i) % n
            player = self.players[next_pos]
            if not player.has_folded and player.stack > 0:
                # In betting round, player needs to act if they haven't matched current bet
                # OR if they haven't acted yet (last_action is None)
                if player.current_bet < self.current_bet or player.last_action is None:
                    return next_pos
        return -1  # No active players who can act


class PokerGame:
    """Texas Hold'em game engine with visual effects support"""
    
    # Standard deck
    RANKS = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
    SUITS = ['♠', '♥', '♦', '♣']
    
    def __init__(self, game_config: Dict[str, Any]):
        """Initialize game with configuration"""
        self.game_id = f"game_{int(time.time() * 1000)}"
        self.config = game_config
        self.state = self._initialize_game_state()
        self.hand_history = []  # List of completed hands with all actions and results
        self._last_phase_change = None  # Track rapid phase transitions
        self._processing_action = False  # Prevent concurrent action processing
        self._action_lock = asyncio.Lock()  # Thread-safe action processing
        self._processed_requests = {}  # Track processed requests by ID {request_id: (timestamp, result)}
        self._request_cache_ttl = 5.0  # 5 seconds TTL for request cache
        self._state_version = 0  # For optimistic locking
        self._chip_movements = []  # Audit trail for all chip movements
        self._state_snapshots = {}  # Store state snapshots for rollback {version: state}
        self._max_snapshots = 10  # Keep last 10 snapshots
        
        logger.info(f"\n{'='*60}\nINITIALIZING NEW GAME: {self.game_id}")
        logger.info(f"Config: {json.dumps(game_config, indent=2)}")
        
        # Log total chips in play
        total_chips = (game_config['heroStack'] + sum(game_config['opponentStacks'])) * game_config['bigBlind']
        logger.info(f"Total chips in play: ${total_chips}")
        logger.info(f"  Hero: {game_config['heroStack']} BB × ${game_config['bigBlind']} = ${game_config['heroStack'] * game_config['bigBlind']}")
        for i, stack in enumerate(game_config['opponentStacks']):
            logger.info(f"  Opponent {i+1}: {stack} BB × ${game_config['bigBlind']} = ${stack * game_config['bigBlind']}")
        
        logger.info(f"{'='*60}\n")
        
    def _initialize_game_state(self) -> GameState:
        """Initialize a new game state"""
        # Create deck
        deck = []
        for rank in self.RANKS:
            for suit in self.SUITS:
                deck.append(f"{rank}{suit}")
        random.shuffle(deck)
        
        # Create players
        players = []
        
        # Hero player (human)
        hero = Player(
            id="hero",
            name="Hero",
            stack=self.config['heroStack'] * self.config['bigBlind'],
            position=0,
            is_ai=False
        )
        players.append(hero)
        
        # AI players
        for i, stack in enumerate(self.config['opponentStacks']):
            ai_player = Player(
                id=f"ai_{i+1}",
                name=f"Player {i+2}",
                stack=stack * self.config['bigBlind'],
                position=i + 1,
                is_ai=True
            )
            players.append(ai_player)
        
        # Validate player count (2-10 players per Texas Hold'em spec)
        if len(players) < 2:
            raise ValueError("Poker game requires at least 2 players")
        if len(players) > 10:
            raise ValueError("Poker game supports maximum 10 players")
        
        # Randomly assign dealer position
        dealer_position = random.randint(0, len(players) - 1)
        
        return GameState(
            game_id=self.game_id,
            phase=GamePhase.WAITING,
            players=players,
            board_cards=[],
            deck=deck,
            pots=[Pot(amount=0, eligible_players=[p.id for p in players])],
            current_bet=0,
            min_raise=self.config['bigBlind'],
            dealer_position=dealer_position,
            action_on=-1,
            big_blind=self.config['bigBlind'],
            small_blind=self.config['bigBlind'] // 2,
            hand_number=0
        )
    
    def start_new_hand(self) -> Dict[str, Any]:
        """Start a new hand with animations"""
        logger.info(f"\n{'='*60}\nSTARTING NEW HAND #{self.state.hand_number + 1}\n{'='*60}")
        
        # Log current game state
        logger.info("Current player states:")
        for p in self.state.players:
            logger.info(f"  {p.name}: stack=${p.stack}, position={p.position}, is_ai={p.is_ai}")
        
        # First check if only one player has chips (game over)
        players_with_chips = [p for p in self.state.players if p.stack > 0]
        
        if len(players_with_chips) <= 1:
            # Game is over - only one player left with chips
            winner = players_with_chips[0] if players_with_chips else None
            logger.info(f"Game over! Winner: {winner.name if winner else 'No winner'}")
            
            return {
                "success": True,
                "game_over": True,
                "winner": winner.id if winner else None,
                "state": self._serialize_state(),
                "animations": [],
                "message": f"Game Over! {winner.name} wins!" if winner else "Game Over!"
            }
        
        self.state.hand_number += 1
        
        # Validate chip integrity at start of hand
        total_chips_start = sum(p.stack for p in self.state.players)
        expected_total = self.config['heroStack'] * self.config['bigBlind']
        for stack in self.config['opponentStacks']:
            expected_total += stack * self.config['bigBlind']
        
        if total_chips_start != expected_total:
            logger.error(f"CHIP INTEGRITY ERROR at start of hand #{self.state.hand_number}!")
            logger.error(f"Expected ${expected_total} total chips, but found ${total_chips_start}")
            logger.error(f"Difference: ${total_chips_start - expected_total} extra chips")
            for p in self.state.players:
                logger.error(f"  {p.name}: stack=${p.stack}")
        
        # Reset betting state (but don't set phase yet - we'll set it to PRE_FLOP later)
        self.state.current_bet = 0
        self.state.min_raise = self.state.big_blind
        
        # Move dealer button (skip players with no chips)
        self.state.dealer_position = self._get_next_active_dealer_position()
        
        # Reset players
        for player in self.state.players:
            player.reset_for_new_hand()
        
        # Shuffle deck
        self.state.deck = []
        for rank in self.RANKS:
            for suit in self.SUITS:
                self.state.deck.append(f"{rank}{suit}")
        random.shuffle(self.state.deck)
        
        # Clear board
        self.state.board_cards = []
        
        # Reset pots
        active_players = [p for p in self.state.players if p.stack > 0]
        self.state.pots = []
        
        # Set phase to PRE_FLOP early to ensure blinds are logged correctly
        self.state.phase = GamePhase.PRE_FLOP
        
        # Post blinds with animations
        animations = []
        
        # Small blind
        sb_position = self._get_small_blind_position()
        sb_player = self.state.players[sb_position]
        sb_amount = min(self.state.small_blind, sb_player.stack)
        self._place_bet(sb_player, sb_amount)
        
        animations.append({
            "type": "blind_post",
            "player_id": sb_player.id,
            "amount": sb_amount,
            "blind_type": "small",
            "delay": 0
        })
        
        # Big blind
        bb_position = self._get_big_blind_position()
        bb_player = self.state.players[bb_position]
        bb_amount = min(self.state.big_blind, bb_player.stack)
        self._place_bet(bb_player, bb_amount)
        
        animations.append({
            "type": "blind_post",
            "player_id": bb_player.id,
            "amount": bb_amount,
            "blind_type": "big",
            "delay": 500
        })
        
        # Deal hole cards with staggered animations
        delay = 1000
        for i in range(2):  # Two cards per player
            for player in self.state.players:
                if player.stack > 0:  # Only deal to players with chips
                    card = self.state.deck.pop()
                    player.hole_cards.append(card)
                    # Log what we're dealing
                    logger.info(f"Dealing card {i} to {player.name}: {'[hidden]' if player.is_ai else card}")
                    animations.append({
                        "type": "deal_card",
                        "player_id": player.id,
                        "card_index": i,
                        "is_hero": not player.is_ai,
                        "card": card if not player.is_ai else None,  # Include card data for hero
                        "delay": delay
                    })
                    delay += 100
                else:
                    logger.info(f"Skipping deal for {player.name} - no chips remaining")
        
        # Set betting amounts (phase already set to PRE_FLOP above)
        self.state.current_bet = self.state.big_blind
        self.state.min_raise = self.state.big_blind
        
        # Now set action to first player after BB
        self.state.action_on = self._get_first_to_act_position()
        
        logger.info(f"\nHAND SETUP COMPLETE:")
        logger.info(f"  Hand number: {self.state.hand_number}")
        logger.info(f"  Dealer: position {self.state.dealer_position} ({self.state.players[self.state.dealer_position].name})")
        logger.info(f"  Small blind: position {sb_position} ({sb_player.name}) - ${sb_amount}")
        logger.info(f"  Big blind: position {bb_position} ({bb_player.name}) - ${bb_amount}")
        logger.info(f"  First to act: position {self.state.action_on} ({self.state.players[self.state.action_on].name if self.state.action_on >= 0 else 'None'})")
        logger.info(f"  Current bet: ${self.state.current_bet}")
        logger.info(f"  Phase: {self.state.phase.name}")
        
        # Ensure board is cleared for new hand (double check)
        if len(self.state.board_cards) > 0:
            logger.error(f"Board cards not cleared! Had {len(self.state.board_cards)} cards: {self.state.board_cards}")
            self.state.board_cards = []
        
        # Reset phase change tracker for new hand
        self._last_phase_change = None
        
        # Add sound effect animation
        animations.append({
            "type": "sound",
            "sound": "shuffle",
            "delay": 0
        })
        
        self.state.pending_animations = animations
        
        # Log hero's hole cards for debugging
        hero = next((p for p in self.state.players if not p.is_ai), None)
        if hero:
            logger.info(f"Hero's hole cards after dealing: {hero.hole_cards}")
        
        return {
            "success": True,
            "state": self._serialize_state(),
            "animations": animations,
            "message": f"Hand #{self.state.hand_number} - Blinds {self.state.small_blind}/{self.state.big_blind}"
        }
    
    async def process_action(self, player_id: str, action: PlayerAction, amount: int = 0, request_id: str = None) -> Dict[str, Any]:
        """Process a player action with animations - now properly async with locking"""
        logger.info(f"\n{'='*50}\nACTION: {player_id} -> {action.value} (${amount}) [request_id: {request_id}]\n{'='*50}")
        
        # Check for duplicate request
        if request_id:
            # Clean up old requests
            self._cleanup_request_cache()
            
            # Check if we've already processed this request
            if request_id in self._processed_requests:
                timestamp, cached_result = self._processed_requests[request_id]
                logger.warning(f"Duplicate request {request_id} detected, returning cached result")
                return cached_result
        
        # Acquire lock for action processing
        async with self._action_lock:
            logger.info(f"Lock acquired for {player_id}'s {action.value}")
            
            # Double-check game state after acquiring lock
            if self.state.phase == GamePhase.GAME_OVER:
                logger.error(f"Game is over, rejecting action from {player_id}")
                return {"success": False, "error": "Game is over"}
            
            # Create state snapshot before processing
            state_version_before = self._state_version
            snapshot = self._create_state_snapshot()
            
            # Validate state before action
            validation_before = self._validate_game_state()
            if not validation_before["valid"]:
                logger.error(f"State validation errors BEFORE action: {validation_before['errors']}")
            if validation_before["warnings"]:
                logger.warning(f"State validation warnings BEFORE action: {validation_before['warnings']}")
            
            try:
                result = self._do_process_action(player_id, action, amount)
                
                # If successful, increment state version and validate
                if result.get("success"):
                    self._state_version += 1
                    
                    # Validate state after action
                    validation_after = self._validate_game_state()
                    if not validation_after["valid"]:
                        logger.error(f"State validation errors AFTER action: {validation_after['errors']}")
                        # Add validation errors to result
                        result["validation_errors"] = validation_after["errors"]
                    if validation_after["warnings"]:
                        logger.warning(f"State validation warnings AFTER action: {validation_after['warnings']}")
                    
                    # Cache successful result if request_id provided
                    if request_id:
                        self._processed_requests[request_id] = (time.time(), result)
                
                return result
            except Exception as e:
                logger.error(f"Error processing action: {e}")
                logger.error(f"Rolling back to state version {state_version_before}")
                # Restore state from snapshot
                if self._restore_state_snapshot(state_version_before):
                    logger.info("Successfully rolled back state")
                else:
                    logger.error("Failed to rollback state - game may be corrupted!")
                return {"success": False, "error": str(e)}
    
    def _do_process_action(self, player_id: str, action: PlayerAction, amount: int = 0) -> Dict[str, Any]:
        """Internal action processing"""
        # CRITICAL: Reject actions if game is over
        if self.state.phase == GamePhase.GAME_OVER:
            logger.error(f"ERROR: Attempted action during GAME_OVER phase!")
            return {"success": False, "error": "Hand is already over"}
        
        # Also reject if we're in WAITING phase (between hands)
        if self.state.phase == GamePhase.WAITING:
            logger.error(f"ERROR: Attempted action during WAITING phase!")
            return {"success": False, "error": "No hand in progress"}
        
        logger.info(f"Game state BEFORE action:")
        logger.info(f"  Phase: {self.state.phase.name}")
        logger.info(f"  Current bet: ${self.state.current_bet}")
        logger.info(f"  Board cards: {self.state.board_cards}")
        # Calculate current pot (including current round bets)
        pot_total = sum(pot.amount for pot in self.state.pots)
        if pot_total == 0:
            # During betting rounds, calculate from player contributions
            pot_total = sum(p.total_bet_this_hand for p in self.state.players)
        logger.info(f"  Pot total: ${pot_total}")
        
        # Log all player states
        logger.info("Player states:")
        for p in self.state.players:
            logger.info(f"  {p.name}: stack=${p.stack}, current_bet=${p.current_bet}, last_action={p.last_action.value if p.last_action else 'None'}, folded={p.has_folded}")
        
        player = self._get_player_by_id(player_id)
        if not player:
            return {"success": False, "error": "Invalid player"}
        
        # CRITICAL: Reject actions from folded players
        if player.has_folded:
            logger.error(f"ERROR: Folded player {player_id} attempted to act!")
            return {"success": False, "error": "Cannot act after folding"}
        
        if self.state.players[self.state.action_on].id != player_id:
            return {"success": False, "error": "Not your turn"}
        
        animations = []
        
        # Process the action
        if action == PlayerAction.FOLD:
            player.has_folded = True
            player.last_action = action
            animations.append({
                "type": "fold",
                "player_id": player_id,
                "delay": 0
            })
            
        elif action == PlayerAction.CHECK:
            # Pre-flop special rules for blinds
            if self.state.phase == GamePhase.PRE_FLOP:
                # Check if this player posted a blind
                bb_position = self._get_big_blind_position()
                sb_position = self._get_small_blind_position()
                
                if player.position == bb_position:
                    # Big blind can check if no one raised beyond the big blind amount
                    if self.state.current_bet > self.state.big_blind:
                        logger.error(f"Big blind cannot check - bet was raised to ${self.state.current_bet}")
                        return {"success": False, "error": "Cannot check, must call or fold"}
                    # BB can check when current bet equals big blind (their posted amount)
                elif player.position == sb_position:
                    # Small blind cannot check pre-flop, must at least call the big blind
                    logger.error(f"Small blind cannot check pre-flop - must call ${self.state.current_bet - player.current_bet}")
                    return {"success": False, "error": "Cannot check, must call or fold"}
                else:
                    # Non-blind players cannot check pre-flop if they haven't matched the big blind
                    if self.state.current_bet > player.current_bet:
                        logger.error(f"Cannot check - must match bet of ${self.state.current_bet}")
                        return {"success": False, "error": "Cannot check, must call or fold"}
            else:
                # Post-flop: standard check rules - can only check if current bet matches
                if self.state.current_bet > player.current_bet:
                    logger.error(f"Cannot check - current bet is ${self.state.current_bet}, player has only bet ${player.current_bet}")
                    return {"success": False, "error": "Cannot check, must call or fold"}
            
            player.last_action = action
            animations.append({
                "type": "check",
                "player_id": player_id,
                "delay": 0
            })
            
        elif action == PlayerAction.CALL:
            to_call = self.state.current_bet - player.current_bet
            call_amount = min(to_call, player.stack)
            
            logger.info(f"{player.name} CALLING: current_bet={self.state.current_bet}, player_bet={player.current_bet}")
            logger.info(f"To call: ${to_call}, Player stack: ${player.stack}, Actual call: ${call_amount}")
            
            # If calling requires entire stack, should be ALL_IN instead
            if call_amount == player.stack and player.stack > 0:
                logger.warning(f"CALL requires entire stack - should be ALL_IN action instead!")
            
            self._place_bet(player, call_amount)
            player.last_action = action
            animations.append({
                "type": "bet",
                "player_id": player_id,
                "amount": call_amount,
                "action": "call",
                "delay": 0
            })
            
        elif action == PlayerAction.RAISE:
            if amount < self.state.min_raise:
                return {"success": False, "error": f"Minimum raise is {self.state.min_raise}"}
            
            raise_to = self.state.current_bet + amount
            bet_amount = min(raise_to - player.current_bet, player.stack)
            
            # Log raise validation
            logger.info(f"RAISE validation: amount={amount}, min_raise={self.state.min_raise}")
            logger.info(f"Current bet: {self.state.current_bet} -> raise to: {raise_to}")
            logger.info(f"Player will bet: {bet_amount} (from current {player.current_bet} to {player.current_bet + bet_amount})")
            
            self._place_bet(player, bet_amount)
            self.state.current_bet = player.current_bet
            # IMPORTANT: min_raise should be at least the amount of this raise
            # This ensures the next player must raise by at least as much
            self.state.min_raise = max(amount, self.state.min_raise)
            player.last_action = action
            
            animations.append({
                "type": "bet",
                "player_id": player_id,
                "amount": bet_amount,
                "action": "raise",
                "delay": 0
            })
            
        elif action == PlayerAction.ALL_IN:
            all_in_amount = player.stack
            logger.info(f"\n*** {player.name} going ALL-IN with ${all_in_amount} ***")
            logger.info(f"Before all-in: current_bet={self.state.current_bet}, player_bet={player.current_bet}")
            logger.info(f"Players in hand BEFORE all-in: {len(self.get_players_in_hand())}")
            
            self._place_bet(player, all_in_amount)
            
            if player.current_bet > self.state.current_bet:
                logger.info(f"Updating table current_bet from {self.state.current_bet} to {player.current_bet}")
                self.state.current_bet = player.current_bet
            else:
                logger.info(f"All-in amount ({player.current_bet}) doesn't exceed current bet ({self.state.current_bet})")
            
            player.last_action = action
            
            # Log state after all-in
            logger.info(f"After all-in: player stack=${player.stack}, player bet=${player.current_bet}")
            logger.info(f"Players who can still act: {[p.name for p in self.state.players if not p.has_folded and p.stack > 0]}")
            
            animations.append({
                "type": "bet",
                "player_id": player_id,
                "amount": all_in_amount,
                "action": "all_in",
                "delay": 0
            })
        
        # Check if only one player remains (others folded)
        players_in_hand = self.get_players_in_hand()
        logger.info(f"Players still in hand after {player.name}'s {action.value}: {len(players_in_hand)}")
        
        if len(players_in_hand) == 1:
            # Everyone else folded - immediate win
            logger.info("All opponents folded - awarding pot to remaining player")
            logger.info(f"Current board: {self.state.board_cards} (phase: {self.state.phase.name})")
            # Calculate final pots
            self._calculate_pots()
            # Award pot to remaining player WITHOUT going to showdown
            winner = players_in_hand[0]
            total_won = 0
            
            for pot in self.state.pots:
                if winner.id in pot.eligible_players:
                    stack_before = winner.stack
                    winner.stack += pot.amount
                    total_won += pot.amount
                    logger.info(f"{winner.name} wins pot of ${pot.amount} (all opponents folded)")
                    self._record_chip_movement(winner.id, pot.amount, "pot_won_fold", stack_before)
            
            if total_won > 0:
                winner._won_amount = total_won
                winner._winning_hand = "All opponents folded"
                animations.append({
                    "type": "award_pot",
                    "winner_id": winner.id,
                    "amount": total_won,
                    "delay": 500,
                    "stack_before_win": winner.stack - total_won
                })
            
            # Clear pots
            self.state.pots = []
            
            # Mark hand as complete
            animations.append({
                "type": "hand_complete",
                "delay": 1000
            })
            
            # Record hand history
            self._record_hand_history()
            
            # Clear all player bets
            for p in self.state.players:
                p.total_bet_this_hand = 0
                p.current_bet = 0
            
            # Set phase to GAME_OVER (for this hand)
            self.state.phase = GamePhase.GAME_OVER
            
            # Clear action_on since hand is over
            self.state.action_on = -1
        elif len(players_in_hand) == 0:
            # This should never happen
            logger.error("ERROR: No players in hand! This should never happen!")
            return {"success": False, "error": "No players remaining in hand"}
        else:
            # Check if betting round is complete
            logger.info(f"\n*** CHECKING IF BETTING ROUND COMPLETE AFTER {player.name}'s {action.value} ***")
            is_complete = self._is_betting_round_complete()
            
            if is_complete:
                # Move to next phase
                logger.info(f"*** BETTING ROUND COMPLETE! Advancing from {self.state.phase.name} ***")
                next_phase_result = self._advance_phase()
                animations.extend(next_phase_result["animations"])
            else:
                # Move to next player
                logger.info(f"*** BETTING ROUND NOT COMPLETE - Finding next player ***")
                next_position = self._get_next_active_position(self.state.action_on)
                logger.info(f"Next player to act: position {next_position}")
                
                if next_position >= 0:
                    next_player = self.state.players[next_position]
                    logger.info(f"Next to act: {next_player.name} (current_bet: ${next_player.current_bet}, needs: ${self.state.current_bet - next_player.current_bet})")
                else:
                    logger.error("ERROR: No next player found! This shouldn't happen!")
                
                self.state.action_on = next_position
        
        self.state.pending_animations = animations
        
        # Final logging
        logger.info(f"\nGame state AFTER action:")
        logger.info(f"  Phase: {self.state.phase.name}")
        logger.info(f"  Current bet: ${self.state.current_bet}")
        logger.info(f"  Board cards: {self.state.board_cards}")
        logger.info(f"  Action on: position {self.state.action_on}")
        logger.info("Player states:")
        for p in self.state.players:
            logger.info(f"  {p.name}: stack=${p.stack}, current_bet=${p.current_bet}, last_action={p.last_action.value if p.last_action else 'None'}, folded={p.has_folded}")
        logger.info(f"{'='*50}\n")
        
        return {
            "success": True,
            "state": self._serialize_state(),
            "animations": animations
        }
    
    def _advance_phase(self) -> Dict[str, Any]:
        """Advance to next game phase with animations"""
        start_time = time.time()
        
        logger.info(f"\n{'='*60}\nPHASE TRANSITION: {self.state.phase.name} -> NEXT\n{'='*60}")
        
        # Check for rapid phase transitions
        if self._last_phase_change:
            time_since_last = start_time - self._last_phase_change
            if time_since_last < 2.0:  # Less than 2 seconds
                logger.error(f"ERROR: RAPID PHASE TRANSITION! Only {time_since_last:.3f}s since last phase change!")
        
        # Log why we're transitioning
        logger.info("TRANSITION REASON: Betting round marked complete")
        logger.info(f"Current state:")
        logger.info(f"  Phase: {self.state.phase.name}")
        logger.info(f"  Board cards: {self.state.board_cards}")
        logger.info(f"  Current bet: ${self.state.current_bet}")
        logger.info("Player betting status:")
        for p in self.get_active_players():
            logger.info(f"  {p.name}: bet=${p.current_bet}, stack=${p.stack}, last_action={p.last_action.value if p.last_action else 'None'}")
        
        animations = []
        
        # Add a phase transition notification
        phase_names = {
            GamePhase.PRE_FLOP: "Flop",
            GamePhase.FLOP: "Turn",
            GamePhase.TURN: "River",
            GamePhase.RIVER: "Showdown"
        }
        next_phase_name = phase_names.get(self.state.phase, "")
        
        # DON'T calculate pots here - only at showdown!
        # Just reset betting for new round
        logger.info("\nRESETTING BETS FOR NEW BETTING ROUND:")
        for player in self.state.players:
            old_bet = player.current_bet
            old_action = player.last_action
            player.current_bet = 0
            # Reset last action for new betting round (except for folded/all-in players)
            if not player.has_folded and player.stack > 0:
                player.last_action = None
                logger.info(f"  {player.name}: bet ${old_bet}->$0, action {old_action.value if old_action else 'None'}->None")
            else:
                logger.info(f"  {player.name}: bet ${old_bet}->$0 (folded={player.has_folded}, all-in={player.stack==0})")
        
        old_current_bet = self.state.current_bet
        self.state.current_bet = 0
        self.state.min_raise = self.state.big_blind
        logger.info(f"Table current bet: ${old_current_bet} -> $0")
        
        if self.state.phase == GamePhase.PRE_FLOP:
            # Sanity check: board should be empty in pre-flop
            if len(self.state.board_cards) > 0:
                logger.error(f"ERROR: Board has {len(self.state.board_cards)} cards in PRE_FLOP phase! Cards: {self.state.board_cards}")
                logger.error("This should never happen - clearing board")
                self.state.board_cards = []
            
            # Advance to FLOP phase
            self.state.phase = GamePhase.FLOP
            logger.info(f"Advanced to FLOP phase. Cards will be dealt on request.")
            
            # Mark that we need cards dealt
            self.state.awaiting_card_deal = True
            
        elif self.state.phase == GamePhase.FLOP:
            # Sanity check: board should have exactly 3 cards in flop
            if len(self.state.board_cards) != 3:
                logger.error(f"ERROR: Board has {len(self.state.board_cards)} cards in FLOP phase, expected 3! Cards: {self.state.board_cards}")
            
            # Advance to TURN phase
            self.state.phase = GamePhase.TURN
            logger.info(f"Advanced to TURN phase. Cards will be dealt on request.")
            
            # Mark that we need cards dealt
            self.state.awaiting_card_deal = True
            
        elif self.state.phase == GamePhase.TURN:
            # Sanity check: board should have exactly 4 cards in turn
            if len(self.state.board_cards) != 4:
                logger.error(f"ERROR: Board has {len(self.state.board_cards)} cards in TURN phase, expected 4! Cards: {self.state.board_cards}")
            
            # Advance to RIVER phase
            self.state.phase = GamePhase.RIVER
            logger.info(f"Advanced to RIVER phase. Cards will be dealt on request.")
            
            # Mark that we need cards dealt
            self.state.awaiting_card_deal = True
            
        elif self.state.phase == GamePhase.RIVER:
            # Before going to showdown, ensure we have all 5 community cards
            if len(self.state.board_cards) != 5:
                logger.error(f"ERROR: Trying to go to showdown with only {len(self.state.board_cards)} board cards!")
                logger.error(f"Board: {self.state.board_cards}")
                logger.error("PREVENTING SHOWDOWN - This is a critical error!")
                # Don't go to showdown with incomplete board
                return {"animations": animations}
            
            # Showdown - only if we have all cards
            logger.info("Moving to SHOWDOWN phase with complete board")
            self.state.phase = GamePhase.SHOWDOWN
            # Calculate final pots before showdown
            self._calculate_pots()
            showdown_result = self._resolve_showdown()
            animations.extend(showdown_result["animations"])
            
            # Record phase change time even for showdown
            self._last_phase_change = time.time()
            logger.info(f"====== PHASE TRANSITION END - SHOWDOWN (took {time.time() - start_time:.3f}s) ======")
            
            return {"animations": animations}
        
        elif self.state.phase == GamePhase.SHOWDOWN:
            logger.error("ERROR: Trying to advance from SHOWDOWN phase!")
            return {"animations": []}
        
        elif self.state.phase == GamePhase.GAME_OVER:
            logger.error("ERROR: Trying to advance from GAME_OVER phase!")
            return {"animations": []}
        
        # Set action to first active player
        self.state.action_on = self._get_first_to_act_position()
        logger.info(f"Action is now on position {self.state.action_on}")
        
        # Check if all players are all-in (no one can act)
        if self.state.action_on == -1:
            active_players = [p for p in self.state.players if not p.has_folded and p.stack > 0]
            players_in_hand = [p for p in self.state.players if not p.has_folded]
            
            # If all remaining players are all-in (including when one will bust the other)
            if len(active_players) == 0 and len(players_in_hand) > 1:
                logger.info("All players are all-in - marking for turn-based card dealing")
                
                # Mark that all players are all-in
                self.state.all_players_all_in = True
                
                # CRITICAL: Calculate pots NOW before phase transitions reset current_bet
                logger.info("Calculating pots immediately for all-in situation")
                self._calculate_pots()
                logger.info(f"Pots calculated: {len(self.state.pots)} pots, total: ${sum(pot.amount for pot in self.state.pots)}")
                
                # Add a visual notification
                animations.append({
                    "type": "delay",
                    "delay": 2000,
                    "message": "All players all-in!"
                })
                
                # Tell frontend to request cards
                animations.append({
                    "type": "request_cards",
                    "phase": self.state.phase.name,
                    "delay": 1000
                })
                
                return {"animations": animations}
        
        # Double-check all players have last_action reset
        for player in self.state.players:
            if not player.has_folded and player.stack > 0:
                logger.info(f"{player.name}: last_action={player.last_action}, current_bet={player.current_bet}")
        
        # Add phase transition sound
        animations.append({
            "type": "sound",
            "sound": "card_flip",
            "delay": 0
        })
        
        # If we're awaiting card deal, add animation to request cards
        if self.state.awaiting_card_deal:
            animations.append({
                "type": "request_cards",
                "phase": self.state.phase.name,
                "delay": 1000
            })
        
        # Update pot display but don't calculate pots yet
        # Just track total contributions for display purposes
        pot_total = sum(pot.amount for pot in self.state.pots)
        for player in self.state.players:
            pot_total += player.total_bet_this_hand
        logger.info(f"Current pot total for display: ${pot_total}")
        
        # Log phase transition for debugging
        logger.info(f"Phase transition complete: {self.state.phase.name} with {len(self.state.board_cards)} board cards")
        logger.info(f"Board cards: {self.state.board_cards}")
        logger.info(f"====== PHASE TRANSITION END (took {time.time() - start_time:.3f}s) ======")
        
        # Update last phase change time
        self._last_phase_change = time.time()
        
        return {"animations": animations}
    
    def deal_next_phase_cards(self) -> Dict[str, Any]:
        """Deal cards for the next phase when requested by frontend"""
        logger.info(f"\n{'='*50}\nDEALING CARDS FOR PHASE: {self.state.phase.name}\n{'='*50}")
        
        animations = []
        
        # Check if cards have already been dealt for this phase
        if self.state.cards_dealt_for_phase.get(self.state.phase, False):
            logger.warning(f"Cards already dealt for phase {self.state.phase.name}")
            return {"success": False, "error": "Cards already dealt for this phase"}
        
        # Check if we should be dealing cards
        if not self.state.awaiting_card_deal:
            logger.warning("Not awaiting card deal")
            return {"success": False, "error": "Not awaiting card deal"}
        
        # Deal cards based on current phase
        if self.state.phase == GamePhase.FLOP:
            # Deal flop (3 cards)
            if len(self.state.board_cards) > 0:
                logger.error(f"ERROR: Board already has {len(self.state.board_cards)} cards!")
                return {"success": False, "error": "Board already has cards"}
            
            # Burn card
            burn = self.state.deck.pop()
            animations.append({"type": "burn_card", "delay": 0})
            
            # Deal 3 flop cards
            for i in range(3):
                card = self.state.deck.pop()
                self.state.board_cards.append(card)
                animations.append({
                    "type": "deal_board_card",
                    "card": card,
                    "position": i,
                    "delay": 500 + (i * 400)
                })
            
            logger.info(f"Dealt flop: {self.state.board_cards}")
            
        elif self.state.phase == GamePhase.TURN:
            # Deal turn (1 card)
            if len(self.state.board_cards) != 3:
                logger.error(f"ERROR: Board has {len(self.state.board_cards)} cards, expected 3")
                return {"success": False, "error": "Invalid board state"}
            
            # Burn card
            burn = self.state.deck.pop()
            animations.append({"type": "burn_card", "delay": 0})
            
            # Deal turn card
            card = self.state.deck.pop()
            self.state.board_cards.append(card)
            animations.append({
                "type": "deal_board_card",
                "card": card,
                "position": 3,
                "delay": 500
            })
            
            logger.info(f"Dealt turn: {card}")
            
        elif self.state.phase == GamePhase.RIVER:
            # Deal river (1 card)
            if len(self.state.board_cards) != 4:
                logger.error(f"ERROR: Board has {len(self.state.board_cards)} cards, expected 4")
                return {"success": False, "error": "Invalid board state"}
            
            # Burn card
            burn = self.state.deck.pop()
            animations.append({"type": "burn_card", "delay": 0})
            
            # Deal river card
            card = self.state.deck.pop()
            self.state.board_cards.append(card)
            animations.append({
                "type": "deal_board_card",
                "card": card,
                "position": 4,
                "delay": 500
            })
            
            logger.info(f"Dealt river: {card}")
            
        else:
            logger.error(f"Cannot deal cards in phase: {self.state.phase.name}")
            return {"success": False, "error": f"Cannot deal cards in {self.state.phase.name} phase"}
        
        # Mark cards as dealt for this phase
        self.state.cards_dealt_for_phase[self.state.phase] = True
        self.state.awaiting_card_deal = False
        
        # If all players are all-in and we just dealt cards, check if we should continue
        if self.state.all_players_all_in:
            # Check if we need to advance to next phase
            # Add longer delays for dramatic effect when all-in
            if self.state.phase == GamePhase.FLOP:
                animations.append({
                    "type": "request_next_cards",
                    "phase": "TURN",
                    "delay": 3500  # Increased from 2000ms
                })
            elif self.state.phase == GamePhase.TURN:
                animations.append({
                    "type": "request_next_cards", 
                    "phase": "RIVER",
                    "delay": 3500  # Increased from 2000ms
                })
            elif self.state.phase == GamePhase.RIVER:
                # Time for showdown
                animations.append({
                    "type": "proceed_to_showdown",
                    "delay": 4000  # Increased from 2000ms for final drama
                })
        
        return {
            "success": True,
            "animations": animations,
            "state": self._serialize_state()
        }
    
    def advance_all_in_phase(self) -> Dict[str, Any]:
        """Advance to next phase when all players are all-in"""
        logger.info(f"Advancing all-in phase from {self.state.phase.name}")
        
        if not self.state.all_players_all_in:
            return {"success": False, "error": "Not in all-in situation"}
        
        # Advance phase
        result = self._advance_phase()
        
        # Add request for next cards if needed
        if self.state.awaiting_card_deal:
            result["animations"].append({
                "type": "request_cards",
                "phase": self.state.phase.name,
                "delay": 1000
            })
        
        return {
            "success": True,
            "animations": result["animations"],
            "state": self._serialize_state()
        }
    
    def _resolve_showdown(self) -> Dict[str, Any]:
        """Resolve showdown and determine winners"""
        logger.info(f"\n{'='*60}\nRESOLVING SHOWDOWN\n{'='*60}")
        logger.info(f"Phase when showdown called: {self.state.phase.name}")
        logger.info(f"Board cards: {self.state.board_cards} (count: {len(self.state.board_cards)})")
        
        # CRITICAL CHECK: Ensure we're actually ready for showdown
        if self.state.phase != GamePhase.SHOWDOWN and self.state.phase != GamePhase.GAME_OVER:
            logger.error(f"ERROR: _resolve_showdown called during {self.state.phase.name} phase!")
            logger.error("This should never happen!")
            return {"animations": []}
        
        # Check if pots have already been cleared (showdown already resolved)
        if not self.state.pots or sum(pot.amount for pot in self.state.pots) == 0:
            logger.warning("Showdown already resolved - no pots to award")
            return {"animations": []}
        
        animations = []
        active_players = self.get_players_in_hand()
        
        # If only one player remains (others folded), they win all pots they're eligible for
        if len(active_players) == 1:
            winner = active_players[0]
            total_won = 0
            
            # Award all pots the winner is eligible for
            for pot in self.state.pots:
                if winner.id in pot.eligible_players:
                    logger.info(f"Before awarding pot: {winner.name} stack=${winner.stack}")
                    stack_before = winner.stack
                    winner.stack += pot.amount
                    total_won += pot.amount
                    logger.info(f"{winner.name} wins pot of ${pot.amount}")
                    logger.info(f"After awarding pot: {winner.name} stack=${winner.stack}")
                    # Record chip movement
                    self._record_chip_movement(winner.id, pot.amount, "pot_won_fold", stack_before)
            
            if total_won > 0:
                # Track winner info for hand history
                winner._won_amount = total_won
                winner._winning_hand = "All opponents folded"
                
                animations.append({
                    "type": "award_pot",
                    "winner_id": winner.id,
                    "amount": total_won,
                    "delay": 500,
                    "stack_before_win": winner.stack - total_won  # Include pre-win stack
                })
            else:
                logger.warning("No pots to award - this shouldn't happen!")
        else:
            # Show all hands with animation
            for i, player in enumerate(active_players):
                if player.is_ai:  # Only reveal AI hands
                    animations.append({
                        "type": "reveal_cards",
                        "player_id": player.id,
                        "cards": player.hole_cards,
                        "delay": i * 500
                    })
            
            # CRITICAL: Only evaluate hands if we have a complete board (5 cards)
            # This prevents premature hand evaluation during all-in situations
            if len(self.state.board_cards) < 5:
                logger.error(f"ERROR: Attempting to evaluate hands with incomplete board! Only {len(self.state.board_cards)} cards dealt!")
                logger.error(f"Board: {self.state.board_cards}")
                logger.error("This should never happen - showdown should only occur after river!")
                # Don't evaluate - return empty animations
                return {"animations": []}
            
            # Evaluate hands and determine winners for each pot
            delay = len(active_players) * 500 + 1000
            
            # Keep track of total winnings for celebration animation
            player_winnings = {p.id: 0 for p in active_players}
            
            for i, pot in enumerate(self.state.pots):
                # Get eligible players for this pot
                eligible_in_pot = [p for p in active_players if p.id in pot.eligible_players]
                
                if eligible_in_pot:
                    # Build hole cards dict for eligible players
                    hole_cards_dict = {p.id: p.hole_cards for p in eligible_in_pot}
                    
                    # Get winners using hand evaluator
                    winner_ids, evaluations = get_winning_players(hole_cards_dict, self.state.board_cards)
                    
                    # Log hand evaluations
                    for player_id, hand_eval in evaluations.items():
                        player = next(p for p in eligible_in_pot if p.id == player_id)
                        logger.info(f"{player.name} has {hand_eval}")
                    
                    # Split pot among winners
                    split_amount = pot.amount // len(winner_ids)
                    remainder = pot.amount % len(winner_ids)
                    
                    for j, winner_id in enumerate(winner_ids):
                        winner = next(p for p in eligible_in_pot if p.id == winner_id)
                        # First winner gets any remainder from integer division
                        award_amount = split_amount + (remainder if j == 0 else 0)
                        stack_before = winner.stack
                        winner.stack += award_amount
                        player_winnings[winner_id] += award_amount
                        # Record chip movement
                        self._record_chip_movement(winner_id, award_amount, f"pot_{i+1}_won_showdown", stack_before)
                        
                        # Track winner info for hand history
                        if not hasattr(winner, '_won_amount'):
                            winner._won_amount = 0
                            winner._winning_hand = evaluations[winner_id].name
                        winner._won_amount += award_amount
                        
                        animations.append({
                            "type": "award_pot",
                            "winner_id": winner_id,
                            "amount": award_amount,
                            "pot_number": i + 1,
                            "delay": delay,
                            "hand_name": evaluations[winner_id].name,
                            "stack_before_win": winner.stack - award_amount  # Include pre-win stack
                        })
                        
                        if len(winner_ids) > 1:
                            logger.info(f"{winner.name} wins ${award_amount} from pot {i+1} (split pot)")
                        else:
                            logger.info(f"{winner.name} wins pot {i+1} of ${award_amount} with {evaluations[winner_id]}")
                    
                    delay += 1000
            
            # Celebration for biggest winner
            if player_winnings:
                biggest_winner_id = max(player_winnings.items(), key=lambda x: x[1])[0]
                if player_winnings[biggest_winner_id] > 0:
                    animations.append({
                        "type": "celebration",
                        "winner_id": biggest_winner_id,
                        "delay": delay
                    })
        
        # DON'T set phase to GAME_OVER yet - let animations play first
        # self.state.phase = GamePhase.GAME_OVER  # REMOVED - causes premature game over screen
        logger.info(f"\n{'='*60}\nHAND COMPLETE - STAYING IN SHOWDOWN PHASE\n{'='*60}")
        logger.info(f"Final board: {self.state.board_cards}")
        
        # Log final player stacks
        busted_players = []
        total_chips_end = 0
        for player in self.state.players:
            logger.info(f"{player.name} final stack: ${player.stack}")
            total_chips_end += player.stack
            if player.stack == 0:
                busted_players.append(player)
        
        # Validate chip integrity
        expected_total = self.config['heroStack'] * self.config['bigBlind']
        for stack in self.config['opponentStacks']:
            expected_total += stack * self.config['bigBlind']
        
        if total_chips_end != expected_total:
            logger.error(f"CHIP INTEGRITY ERROR: Expected ${expected_total} total chips, but found ${total_chips_end}!")
            logger.error(f"Difference: ${total_chips_end - expected_total} extra chips created!")
        
        # If someone got busted, add extra delay so players can see why
        if busted_players:
            logger.info(f"Player(s) busted: {[p.name for p in busted_players]}")
            # Add a longer delay with a clear message about who won and why
            busted_names = ", ".join([p.name for p in busted_players])
            # Calculate total animation time to ensure board is visible
            total_animation_time = sum(a.get('delay', 0) for a in animations)
            animations.append({
                "type": "delay",
                "delay": max(6000, total_animation_time + 3000),  # Ensure enough time to see board
                "message": f"{busted_names} eliminated! Final board shown above."
            })
        
        # Add a final animation to signal hand is complete
        animations.append({
            "type": "hand_complete",
            "delay": 500
        })
        
        # Record hand history
        self._record_hand_history()
        
        # Clear pots to prevent double-awarding
        self.state.pots = []
        
        # Clear all player bets
        for p in self.state.players:
            p.total_bet_this_hand = 0
            p.current_bet = 0
        
        return {"animations": animations}
    
    def _place_bet(self, player: Player, amount: int):
        """Place a bet for a player"""
        actual_bet = min(amount, player.stack)
        
        logger.info(f"_place_bet: {player.name} betting ${actual_bet} (requested ${amount})")
        logger.info(f"Before: stack=${player.stack}, current_bet=${player.current_bet}")
        
        # Record state before the bet
        stack_before = player.stack
        
        player.stack -= actual_bet
        player.current_bet += actual_bet
        player.total_bet_this_hand += actual_bet
        
        logger.info(f"After: stack=${player.stack}, current_bet=${player.current_bet}, total_bet_this_hand=${player.total_bet_this_hand}")
        
        # Record chip movement
        self._record_chip_movement(player.id, -actual_bet, f"bet_{self.state.phase.name}", stack_before)
        
        # Don't add to pot here - we'll calculate pots when betting round ends
        # This allows proper side pot calculation
    
    def _is_betting_round_complete(self) -> bool:
        """Check if current betting round is complete"""
        # CRITICAL: Use players IN HAND, not just those with chips!
        # All-in players are still in the hand and others must match their bets
        players_in_hand = self.get_players_in_hand()
        active_players = [p for p in players_in_hand if p.stack > 0]  # Can still act
        
        logger.info(f"\n{'*'*50}\nBETTING ROUND COMPLETION CHECK\n{'*'*50}")
        logger.info(f"Phase: {self.state.phase.name}")
        logger.info(f"Current table bet: ${self.state.current_bet}")
        logger.info(f"Players in hand: {len(players_in_hand)} (includes all-in)")
        logger.info(f"Players who can act: {len(active_players)} (have chips)")
        
        # If everyone has folded except one player, round is complete
        if len(players_in_hand) <= 1:
            logger.info("Only one player remains in hand - round complete")
            return True
        
        # If no one can act (everyone is all-in), round is complete
        if len(active_players) == 0:
            logger.info("All players are all-in - round complete")
            return True
        
        # For a betting round to be complete, ALL active players must have:
        # 1. Acted at least once (last_action != None) AND
        # 2. Either matched the current bet OR are all-in
        
        players_who_need_to_act = 0
        highest_bet_player = None
        highest_bet = 0
        
        # First, find who made the highest bet (including all-in players)
        for player in players_in_hand:
            if player.current_bet > highest_bet:
                highest_bet = player.current_bet
                highest_bet_player = player.name
        
        logger.info(f"Highest bet: ${highest_bet} by {highest_bet_player}")
        
        # Now check each player who can still act
        for player in active_players:  # Only check those with chips
            # All-in players don't need to act
            if player.stack == 0:
                logger.info(f"{player.name}: All-in (stack=0) - no action needed")
                continue
            
            # Player needs to act if they haven't acted yet
            if player.last_action is None:
                players_who_need_to_act += 1
                logger.info(f"{player.name}: Hasn't acted yet (last_action=None) - NEEDS TO ACT")
                continue
            
            # Player needs to act if they haven't matched the current bet
            if player.current_bet < self.state.current_bet:
                players_who_need_to_act += 1
                logger.info(f"{player.name}: Bet ${player.current_bet} < table bet ${self.state.current_bet} - NEEDS TO ACT")
                continue
            
            # Special case: In pre-flop, big blind gets option to raise even if matched
            if (self.state.phase == GamePhase.PRE_FLOP and 
                player.position == self._get_big_blind_position() and 
                player == highest_bet_player and
                player.last_action is None):
                players_who_need_to_act += 1
                logger.info(f"{player.name}: Big blind option to raise - NEEDS TO ACT")
                continue
            
            logger.info(f"{player.name}: Has acted and matched bet - no action needed")
        
        logger.info(f"\nSUMMARY:")
        logger.info(f"  Players who need to act: {players_who_need_to_act}")
        logger.info(f"  Betting round complete: {players_who_need_to_act == 0}")
        
        if players_who_need_to_act == 0 and self.state.current_bet > 0:
            logger.info(f"  All players have matched the bet of ${self.state.current_bet}")
        
        logger.info(f"{'*'*50}\n")
        
        return players_who_need_to_act == 0
    
    def _calculate_pots(self):
        """Calculate main pot and side pots based on current bets
        
        This should only be called ONCE at the end of all betting, just before showdown.
        It should NOT be called after each betting round.
        """
        logger.info("\nCALCULATING POTS:")
        
        # If pots already exist (e.g., calculated during all-in), don't recalculate
        if self.state.pots and sum(pot.amount for pot in self.state.pots) > 0:
            logger.info(f"Pots already calculated: {len(self.state.pots)} pots, total ${sum(pot.amount for pot in self.state.pots)}")
            return
        
        # First check if everyone folded to one player
        remaining_players = [p for p in self.state.players if not p.has_folded]
        if len(remaining_players) == 1:
            # Everyone else folded - handle uncalled bets
            winner = remaining_players[0]
            folded_bets = [p.total_bet_this_hand for p in self.state.players if p.has_folded and p.total_bet_this_hand > 0]
            
            if folded_bets:
                # The maximum anyone called is the highest bet from folded players
                max_called = max(folded_bets)
                
                # Winner collects the called amount from all players
                pot_size = 0
                for p in self.state.players:
                    # Each player contributes up to the max called amount
                    contribution = min(p.total_bet_this_hand, max_called)
                    pot_size += contribution
                    logger.info(f"  {p.name} contributes ${contribution} to pot (bet ${p.total_bet_this_hand})")
                
                # Create pot with only the called amounts
                self.state.pots = [Pot(amount=pot_size, eligible_players=[winner.id])]
                logger.info(f"Everyone folded. Pot: ${pot_size} (max called: ${max_called})")
                
                # Return uncalled portion to the winner IMMEDIATELY
                uncalled = winner.total_bet_this_hand - max_called
                if uncalled > 0:
                    stack_before = winner.stack
                    winner.stack += uncalled
                    logger.info(f"Returned uncalled bet of ${uncalled} to {winner.name}")
                    logger.info(f"{winner.name} stack after uncalled return: ${winner.stack}")
                    # Record chip movement
                    self._record_chip_movement(winner.id, uncalled, "uncalled_bet_return", stack_before)
                
                # Don't clear bets yet - they're needed for pot awarding
                # Will be cleared after pot is awarded
            else:
                # No one else had any bets (e.g., everyone folded pre-flop to BB)
                # Winner just gets their own bet back
                self.state.pots = []
                stack_before = winner.stack
                winner.stack += winner.total_bet_this_hand
                # Record chip movement
                self._record_chip_movement(winner.id, winner.total_bet_this_hand, "own_bet_return", stack_before)
                logger.info(f"No callers. Returned ${winner.total_bet_this_hand} to {winner.name}")
                # Clear all bets
                for p in self.state.players:
                    p.total_bet_this_hand = 0
            return
        
        # Get all unique bet amounts from players who haven't folded
        bet_amounts = []
        for p in self.state.players:
            # Use total_bet_this_hand to get total contributions for the entire hand
            if p.total_bet_this_hand > 0 and not p.has_folded:
                if p.total_bet_this_hand not in bet_amounts:
                    bet_amounts.append(p.total_bet_this_hand)
                logger.info(f"  {p.name}: total bet this hand ${p.total_bet_this_hand}, folded={p.has_folded}")
        
        # Sort bet amounts ascending
        bet_amounts.sort()
        
        # Clear existing pots and recalculate
        self.state.pots = []
        previous_level = 0
        
        for bet_level in bet_amounts:
            pot_amount = 0
            eligible_players = []
            
            # Calculate contributions for this pot level
            for p in self.state.players:
                if p.total_bet_this_hand > previous_level:
                    # Player contributes the difference between levels, up to their total bet
                    contribution = min(bet_level - previous_level, p.total_bet_this_hand - previous_level)
                    pot_amount += contribution
                    
                    # Player is eligible if they haven't folded and bet at least this level
                    if not p.has_folded and p.total_bet_this_hand >= bet_level:
                        eligible_players.append(p.id)
            
            if pot_amount > 0 and eligible_players:
                pot = Pot(amount=pot_amount, eligible_players=eligible_players)
                self.state.pots.append(pot)
                logger.info(f"Pot {len(self.state.pots)}: ${pot_amount} - Eligible: {eligible_players}")
            
            previous_level = bet_level
        
        # Log total pot info
        total_pot = sum(pot.amount for pot in self.state.pots)
        logger.info(f"Total pots: {len(self.state.pots)}, Total amount: ${total_pot}")
        
        # Validate pot total
        total_chips_in_play = sum(p.stack for p in self.state.players) + sum(p.total_bet_this_hand for p in self.state.players)
        if total_pot > total_chips_in_play:
            logger.error(f"ERROR: Pot total ${total_pot} exceeds total chips in play ${total_chips_in_play}!")
            logger.error("This indicates a serious bug in pot calculation!")
        
        # Also validate against expected total from config
        expected_total = self.config['heroStack'] * self.config['bigBlind']
        for stack in self.config['opponentStacks']:
            expected_total += stack * self.config['bigBlind']
        
        if total_pot != sum(p.total_bet_this_hand for p in self.state.players):
            logger.error(f"ERROR: Pot total ${total_pot} doesn't match sum of bets ${sum(p.total_bet_this_hand for p in self.state.players)}!")
        
        if total_chips_in_play != expected_total:
            logger.error(f"CHIP INTEGRITY ERROR in pot calculation: Expected ${expected_total} total chips, but found ${total_chips_in_play}!")
            logger.error(f"Player details:")
            for p in self.state.players:
                logger.error(f"  {p.name}: stack=${p.stack}, total_bet_this_hand=${p.total_bet_this_hand}")
    
    def _get_small_blind_position(self) -> int:
        """Get small blind position"""
        active_players = [p for p in self.state.players if p.stack > 0]
        if len(active_players) <= 2:
            # Heads up: dealer is small blind
            return self.state.dealer_position
        
        # Find next active player after dealer
        n = len(self.state.players)
        for i in range(1, n + 1):
            pos = (self.state.dealer_position + i) % n
            if self.state.players[pos].stack > 0:
                return pos
        return self.state.dealer_position
    
    def _get_big_blind_position(self) -> int:
        """Get big blind position"""
        active_players = [p for p in self.state.players if p.stack > 0]
        if len(active_players) <= 2:
            # Heads up: non-dealer is big blind
            n = len(self.state.players)
            for i in range(1, n + 1):
                pos = (self.state.dealer_position + i) % n
                if self.state.players[pos].stack > 0:
                    return pos
        
        # Find second active player after dealer
        n = len(self.state.players)
        active_count = 0
        for i in range(1, n + 1):
            pos = (self.state.dealer_position + i) % n
            if self.state.players[pos].stack > 0:
                active_count += 1
                if active_count == 2:
                    return pos
        return self.state.dealer_position
    
    def _get_first_to_act_position(self) -> int:
        """Get first to act position for current phase"""
        if self.state.phase == GamePhase.PRE_FLOP:
            # Pre-flop: first after big blind
            start = (self._get_big_blind_position() + 1) % len(self.state.players)
            logger.info(f"PRE_FLOP: Looking for first to act after BB position {self._get_big_blind_position()}")
        else:
            # Post-flop: first after dealer
            start = (self.state.dealer_position + 1) % len(self.state.players)
            logger.info(f"POST_FLOP ({self.state.phase.name}): Looking for first to act after dealer position {self.state.dealer_position}")
        
        # Find first active player from start position
        for i in range(len(self.state.players)):
            pos = (start + i) % len(self.state.players)
            player = self.state.players[pos]
            if not player.has_folded and player.stack > 0:
                logger.info(f"First to act: {player.name} at position {pos}")
                return pos
        
        # This is normal when all players are all-in
        logger.info("No active players found to act (all players are all-in or folded)")
        return -1  # Explicitly return -1 when no one can act
    
    def _get_next_active_position(self, current: int) -> int:
        """Get next active player position"""
        return self.state.get_next_active_position(current)
    
    def _get_next_active_dealer_position(self) -> int:
        """Get next dealer position, skipping players with no chips"""
        n = len(self.state.players)
        for i in range(1, n + 1):
            next_pos = (self.state.dealer_position + i) % n
            if self.state.players[next_pos].stack > 0:
                return next_pos
        return self.state.dealer_position  # Shouldn't happen if game continues
    
    def _get_player_by_id(self, player_id: str) -> Optional[Player]:
        """Get player by ID"""
        for player in self.state.players:
            if player.id == player_id:
                return player
        return None
    
    def get_players_in_hand(self) -> List[Player]:
        """Get all players still in the hand"""
        return self.state.get_players_in_hand()
    
    def get_active_players(self) -> List[Player]:
        """Get all active players"""
        return self.state.get_active_players()
    
    def _record_hand_history(self):
        """Record the completed hand in history"""
        hand_record = {
            "hand_number": self.state.hand_number,
            "timestamp": datetime.now().isoformat(),
            "board_cards": self.state.board_cards.copy(),
            "pots": [
                {
                    "amount": pot.amount,
                    "eligible_players": pot.eligible_players.copy()
                }
                for pot in self.state.pots
            ],
            "players": []
        }
        
        # Record each player's final state
        for player in self.state.players:
            player_record = {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "hole_cards": player.hole_cards.copy() if player.hole_cards else [],
                "final_stack": player.stack,
                "total_bet": player.total_bet_this_hand,
                "folded": player.has_folded,
                "is_dealer": player.position == self.state.dealer_position,
                "is_small_blind": player.position == self._get_small_blind_position(),
                "is_big_blind": player.position == self._get_big_blind_position()
            }
            
            # Add winner information if available
            if hasattr(player, '_won_amount'):
                player_record["won_amount"] = player._won_amount
                player_record["winning_hand"] = player._winning_hand
            
            hand_record["players"].append(player_record)
        
        # Add to history
        self.hand_history.append(hand_record)
        
        # Log hand summary
        logger.info(f"\nHAND #{hand_record['hand_number']} RECORDED IN HISTORY")
        logger.info(f"Board: {' '.join(hand_record['board_cards'])}")
        for p in hand_record['players']:
            if 'won_amount' in p:
                logger.info(f"  {p['name']} won ${p['won_amount']} with {p.get('winning_hand', 'unknown')}")
            elif p['folded']:
                logger.info(f"  {p['name']} folded")
            else:
                logger.info(f"  {p['name']} lost with {' '.join(p['hole_cards'])}")
    
    def get_hand_history(self) -> List[Dict[str, Any]]:
        """Get the complete hand history"""
        return self.hand_history.copy()
    
    def _cleanup_request_cache(self):
        """Remove expired requests from cache"""
        current_time = time.time()
        expired_requests = [
            req_id for req_id, (timestamp, _) in self._processed_requests.items()
            if current_time - timestamp > self._request_cache_ttl
        ]
        for req_id in expired_requests:
            del self._processed_requests[req_id]
            logger.debug(f"Cleaned up expired request: {req_id}")
    
    def _validate_chip_integrity(self, checkpoint: str):
        """Validate that total chips in play match expected amount"""
        total_chips = sum(p.stack for p in self.state.players)
        # Add chips currently bet (both current round and total for hand)
        for p in self.state.players:
            total_chips += p.total_bet_this_hand  # Use total bet for entire hand
            
        expected_total = self.config['heroStack'] * self.config['bigBlind']
        for stack in self.config['opponentStacks']:
            expected_total += stack * self.config['bigBlind']
            
        if total_chips != expected_total:
            logger.error(f"CHIP INTEGRITY ERROR at {checkpoint}!")
            logger.error(f"Expected ${expected_total}, found ${total_chips}")
            logger.error(f"Difference: ${total_chips - expected_total}")
            logger.error("Player details:")
            for p in self.state.players:
                logger.error(f"  {p.name}: stack=${p.stack}, current_bet=${p.current_bet}, total_bet_this_hand=${p.total_bet_this_hand}")
            # Log last few chip movements
            if self._chip_movements:
                logger.error("Recent chip movements:")
                for movement in self._chip_movements[-5:]:
                    logger.error(f"  {movement}")
    
    def _record_chip_movement(self, player_id: str, amount: int, reason: str, state_before: int):
        """Record chip movement for audit trail"""
        player = self._get_player_by_id(player_id)
        if player:
            movement = {
                "timestamp": time.time(),
                "hand_number": self.state.hand_number,
                "player_id": player_id,
                "player_name": player.name,
                "amount": amount,
                "reason": reason,
                "stack_before": state_before,
                "stack_after": player.stack,
                "state_version": self._state_version
            }
            self._chip_movements.append(movement)
            logger.debug(f"Chip movement: {player.name} {amount:+d} ({reason}) [{state_before} -> {player.stack}]")
    
    def _validate_game_state(self) -> Dict[str, Any]:
        """Comprehensive state validation"""
        errors = []
        warnings = []
        
        # 1. Validate chip integrity
        total_chips = sum(p.stack for p in self.state.players)
        for p in self.state.players:
            total_chips += p.total_bet_this_hand  # Use total bet for entire hand
            
        expected_total = self.config['heroStack'] * self.config['bigBlind']
        for stack in self.config['opponentStacks']:
            expected_total += stack * self.config['bigBlind']
            
        if total_chips != expected_total:
            errors.append(f"Chip integrity error: expected ${expected_total}, found ${total_chips}")
        
        # 2. Validate player states
        for player in self.state.players:
            if player.stack < 0:
                errors.append(f"{player.name} has negative stack: ${player.stack}")
            if player.current_bet < 0:
                errors.append(f"{player.name} has negative current bet: ${player.current_bet}")
            if player.has_folded and player.current_bet > 0:
                warnings.append(f"{player.name} has folded but still has bet: ${player.current_bet}")
        
        # 3. Validate action position
        if self.state.phase not in [GamePhase.GAME_OVER, GamePhase.WAITING, GamePhase.SHOWDOWN]:
            # In all-in situations, action_on can be -1 (no one can act)
            if self.state.all_players_all_in and self.state.action_on == -1:
                # This is expected - all players are all-in
                pass
            elif self.state.action_on < 0 or self.state.action_on >= len(self.state.players):
                errors.append(f"Invalid action position: {self.state.action_on}")
            else:
                action_player = self.state.players[self.state.action_on]
                if action_player.has_folded:
                    errors.append(f"Action is on folded player: {action_player.name}")
                if action_player.stack == 0:
                    warnings.append(f"Action is on all-in player: {action_player.name}")
        
        # 4. Validate betting state
        if self.state.current_bet < 0:
            errors.append(f"Current bet is negative: ${self.state.current_bet}")
        if self.state.min_raise < self.state.big_blind:
            warnings.append(f"Min raise ({self.state.min_raise}) is less than big blind ({self.state.big_blind})")
        
        # 5. Validate phase consistency
        board_count = len(self.state.board_cards)
        expected_cards = {
            GamePhase.PRE_FLOP: 0,
            GamePhase.FLOP: 3,
            GamePhase.TURN: 4,
            GamePhase.RIVER: 5,
            GamePhase.SHOWDOWN: 5,
            GamePhase.GAME_OVER: 5,
            GamePhase.WAITING: 0
        }
        if self.state.phase in expected_cards:
            expected = expected_cards[self.state.phase]
            # Don't validate board cards if we're awaiting card deal (all-in situation)
            if board_count != expected and not self.state.awaiting_card_deal and not (self.state.phase == GamePhase.GAME_OVER and board_count < 5):
                errors.append(f"Phase {self.state.phase.name} expects {expected} board cards, found {board_count}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "state_version": self._state_version
        }
    
    def _create_state_snapshot(self) -> Dict[str, Any]:
        """Create a deep copy snapshot of the current game state"""
        import copy
        
        snapshot = {
            "state": copy.deepcopy(self.state),
            "state_version": self._state_version,
            "timestamp": time.time(),
            "chip_movements_count": len(self._chip_movements)
        }
        
        # Store snapshot
        self._state_snapshots[self._state_version] = snapshot
        
        # Clean up old snapshots if we have too many
        if len(self._state_snapshots) > self._max_snapshots:
            oldest_versions = sorted(self._state_snapshots.keys())[:-self._max_snapshots]
            for version in oldest_versions:
                del self._state_snapshots[version]
                logger.debug(f"Removed old snapshot version {version}")
        
        logger.debug(f"Created state snapshot v{self._state_version}, total snapshots: {len(self._state_snapshots)}")
        return snapshot
    
    def _restore_state_snapshot(self, version: int) -> bool:
        """Restore game state from a snapshot"""
        if version not in self._state_snapshots:
            logger.error(f"Snapshot version {version} not found")
            return False
        
        import copy
        snapshot = self._state_snapshots[version]
        
        # Restore state
        self.state = copy.deepcopy(snapshot["state"])
        self._state_version = snapshot["state_version"]
        
        # Trim chip movements to match snapshot
        snapshot_movements_count = snapshot["chip_movements_count"]
        self._chip_movements = self._chip_movements[:snapshot_movements_count]
        
        logger.info(f"Restored state to version {version} from {time.time() - snapshot['timestamp']:.2f}s ago")
        return True
    
    def _serialize_state(self) -> Dict[str, Any]:
        """Serialize game state for client"""
        # Calculate current pot total (all money bet in this hand)
        current_pot_total = 0
        
        # Debug logging for hole cards
        for p in self.state.players:
            if p.id == "hero":
                logger.info(f"Serializing hero: is_ai={p.is_ai}, hole_cards={p.hole_cards}, phase={self.state.phase.name}")
        
        # Since we only calculate pots at showdown, during betting we need to
        # show the total of all bets made this hand
        if self.state.phase in [GamePhase.SHOWDOWN, GamePhase.GAME_OVER]:
            # At showdown, pots have been calculated
            for pot in self.state.pots:
                current_pot_total += pot.amount
        else:
            # During betting, sum all player contributions
            for player in self.state.players:
                current_pot_total += player.total_bet_this_hand
        
        return {
            "game_id": self.state.game_id,
            "phase": self.state.phase.name,
            "hand_number": self.state.hand_number,
            "awaiting_card_deal": self.state.awaiting_card_deal,
            "all_players_all_in": self.state.all_players_all_in,
            "players": [
                {
                    "id": p.id,
                    "name": p.name,
                    "stack": p.stack,
                    "position": p.position,
                    "is_ai": p.is_ai,
                    "is_active": p.is_active,
                    "has_folded": p.has_folded,
                    "hole_cards": p.hole_cards if not p.is_ai or self.state.phase == GamePhase.SHOWDOWN else ["?", "?"],
                    "current_bet": p.current_bet,
                    "last_action": p.last_action.value if p.last_action else None,
                    "is_dealer": p.position == self.state.dealer_position,
                    "is_small_blind": p.position == self._get_small_blind_position(),
                    "is_big_blind": p.position == self._get_big_blind_position()
                }
                for p in self.state.players
            ],
            "board_cards": self.state.board_cards,
            "pots": [
                {"amount": pot.amount, "eligible_players": pot.eligible_players}
                for pot in self.state.pots
            ],
            "current_bet": self.state.current_bet,
            "min_raise": self.state.min_raise,
            "action_on": self.state.action_on,
            "big_blind": self.state.big_blind,
            "small_blind": self.state.small_blind,
            "current_pot_total": current_pot_total  # Add total pot for display
        }