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