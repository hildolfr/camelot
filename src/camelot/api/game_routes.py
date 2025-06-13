"""Game API routes for poker game functionality."""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..game.poker_game import PokerGame, PlayerAction
from ..game.ai_player import AIPlayer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/game", tags=["game"])

# In-memory game storage (in production, use Redis or similar)
active_games: Dict[str, PokerGame] = {}


class GameStartRequest(BaseModel):
    players: int
    heroStack: int
    opponentStacks: List[int]
    difficulty: str
    bigBlind: int


class PlayerActionRequest(BaseModel):
    player_id: str
    action: str
    amount: int = 0


class AIActionRequest(BaseModel):
    player_id: str


@router.post("/start")
async def start_game(request: GameStartRequest) -> Dict[str, Any]:
    """Start a new poker game."""
    try:
        # Create game configuration
        config = request.dict()
        
        # Create new game instance
        game = PokerGame(config)
        
        # Store game
        active_games[game.game_id] = game
        
        # Return initial state
        return {
            "success": True,
            "state": game._serialize_state(),
            "game_id": game.game_id
        }
    except Exception as e:
        logger.error(f"Error starting game: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/new-hand")
async def start_new_hand(game_id: str) -> Dict[str, Any]:
    """Start a new hand in the game."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        result = game.start_new_hand()
        return result
    except Exception as e:
        logger.error(f"Error starting new hand: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/action")
async def process_player_action(game_id: str, request: PlayerActionRequest) -> Dict[str, Any]:
    """Process a player action."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        # Convert string action to PlayerAction enum
        action = PlayerAction(request.action)
        
        # Process the action
        result = game.process_action(request.player_id, action, request.amount)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Invalid action"))
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid action: {request.action}")
    except Exception as e:
        logger.error(f"Error processing player action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/ai-action")
async def process_ai_action(game_id: str, request: AIActionRequest) -> Dict[str, Any]:
    """Process an AI player's action."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        # Get AI player
        ai_player = None
        for player in game.state.players:
            if player.id == request.player_id and player.is_ai:
                ai_player = player
                break
        
        if not ai_player:
            raise HTTPException(status_code=404, detail="AI player not found")
        
        # Create AI instance and get decision
        ai = AIPlayer(game.config.get('difficulty', 'medium'))
        action, amount = ai.decide_action(game.state, ai_player)
        
        # Process the action
        result = game.process_action(request.player_id, action, amount)
        
        return result
    except Exception as e:
        logger.error(f"Error processing AI action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{game_id}/state")
async def get_game_state(game_id: str) -> Dict[str, Any]:
    """Get current game state."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {
        "success": True,
        "state": game._serialize_state()
    }


@router.post("/{game_id}/deal-next-cards")
async def deal_next_cards(game_id: str) -> Dict[str, Any]:
    """Deal cards for the next phase."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        result = game.deal_next_phase_cards()
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Cannot deal cards"))
        return result
    except Exception as e:
        logger.error(f"Error dealing next cards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{game_id}/advance-all-in-phase")
async def advance_all_in_phase(game_id: str) -> Dict[str, Any]:
    """Advance to next phase in all-in situation."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        result = game.advance_all_in_phase()
        if not result.get("success", False):
            raise HTTPException(status_code=400, detail=result.get("error", "Cannot advance phase"))
        return result
    except Exception as e:
        logger.error(f"Error advancing all-in phase: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{game_id}/hand-strength/{player_id}")
async def get_hand_strength(game_id: str, player_id: str) -> Dict[str, Any]:
    """Get current hand strength for a player."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        # Get player
        player = None
        for p in game.state.players:
            if p.id == player_id:
                player = p
                break
        
        if not player:
            raise HTTPException(status_code=404, detail="Player not found")
        
        # Only calculate if player has cards
        if not player.hole_cards or len(player.hole_cards) != 2:
            return {
                "success": True,
                "has_cards": False
            }
        
        # Import calculator
        from ..core.cached_poker_calculator import get_cached_calculator
        calculator = get_cached_calculator()
        
        # Count active opponents
        active_opponents = sum(1 for p in game.state.players if p.id != player_id and not p.has_folded)
        
        # Calculate pot odds
        pot_size = sum(pot.amount for pot in game.state.pots)
        to_call = max(0, game.state.current_bet - player.current_bet)
        pot_odds = to_call / (pot_size + to_call) if (pot_size + to_call) > 0 else 0
        
        # Calculate win probability
        result = calculator.calculate(
            hero_hand=player.hole_cards,
            num_opponents=active_opponents,
            board_cards=game.state.board_cards if game.state.board_cards else None,
            simulation_mode="fast",
            pot_size=pot_size,
            action_to_hero="bet" if to_call > 0 else "check",
            bet_size=to_call / pot_size if pot_size > 0 and to_call > 0 else 0
        )
        
        # Get current hand evaluation if board cards exist
        hand_name = None
        if game.state.board_cards and len(game.state.board_cards) >= 3:
            from ..core.hand_evaluator import evaluate_hand
            eval_result = evaluate_hand(player.hole_cards, game.state.board_cards)
            hand_name = eval_result.name
        
        return {
            "success": True,
            "has_cards": True,
            "win_probability": result.get("win_probability", 0),
            "tie_probability": result.get("tie_probability", 0),
            "current_hand": hand_name,
            "hand_categories": result.get("hand_category_frequencies", {}),
            "pot_odds": pot_odds,
            "to_call": to_call,
            "pot_size": pot_size,
            "equity_needed": result.get("equity_needed", pot_odds),
            "pot_odds_percentage": round(pot_odds * 100, 1),
            "has_direct_odds": result.get("win_probability", 0) > pot_odds if to_call > 0 else None
        }
        
    except Exception as e:
        logger.error(f"Error calculating hand strength: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{game_id}/hand-history")
async def get_hand_history(game_id: str) -> Dict[str, Any]:
    """Get the hand history for a game."""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        history = game.get_hand_history()
        return {
            "success": True,
            "game_id": game_id,
            "total_hands": len(history),
            "hands": history
        }
    except Exception as e:
        logger.error(f"Error getting hand history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{game_id}")
async def end_game(game_id: str) -> Dict[str, Any]:
    """End a game and clean up."""
    if game_id in active_games:
        del active_games[game_id]
        return {"success": True, "message": "Game ended"}
    else:
        raise HTTPException(status_code=404, detail="Game not found")


@router.post("/{game_id}/bug-report")
async def submit_bug_report(game_id: str, bug_report: dict = Body(...)):
    """Submit a bug report for a game"""
    game = active_games.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Log the bug report to the game's log file
    from src.camelot.game.poker_game import logger
    
    # Create a special bug report log entry with searchable marker
    logger.error(f"\n{'='*80}")
    logger.error(f"USER_BUG_REPORT_START")
    logger.error(f"{'='*80}")
    logger.error(f"Game ID: {game_id}")
    logger.error(f"Timestamp: {bug_report.get('timestamp', 'Unknown')}")
    logger.error(f"User Report: {bug_report.get('report', 'No description provided')}")
    logger.error(f"Game Phase: {bug_report.get('game_state', {}).get('phase', 'Unknown')}")
    logger.error(f"Hand Number: {bug_report.get('game_state', {}).get('hand_number', 'Unknown')}")
    logger.error(f"Active Players: {len([p for p in bug_report.get('game_state', {}).get('players', []) if not p.get('has_folded', False)])}")
    logger.error(f"Current Bet: ${bug_report.get('game_state', {}).get('current_bet', 0)}")
    logger.error(f"Board Cards: {bug_report.get('game_state', {}).get('board_cards', [])}")
    logger.error(f"USER_BUG_REPORT_END")
    logger.error(f"{'='*80}\n")
    
    return {"success": True, "message": "Bug report submitted successfully"}