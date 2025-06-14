"""Game API routes for poker game functionality."""

from fastapi import APIRouter, HTTPException, Body, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
import asyncio
import time

from ..game.poker_game import PokerGame, PlayerAction
from ..game.ai_player import AIPlayer
from ..core.game_monitor import game_monitor
from ..core.websocket_manager import websocket_manager

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
    request_id: Optional[str] = None  # For deduplication


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
        
        # Broadcast new hand to all connected players
        if result.get("success"):
            await websocket_manager.broadcast_to_game(game_id, {
                "type": "new_hand",
                "state": result["state"],
                "animations": result.get("animations", []),
                "message": result.get("message", "New hand started")
            })
        
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
        
        # Check if this is a duplicate request
        is_duplicate = False
        if request.request_id and hasattr(game, '_processed_requests'):
            is_duplicate = request.request_id in game._processed_requests
        
        # Record the request
        game_monitor.record_request(
            game_id=game_id,
            player_id=request.player_id,
            action=request.action,
            request_id=request.request_id,
            is_duplicate=is_duplicate
        )
        
        # Process the action with request_id if provided
        result = await game.process_action(request.player_id, action, request.amount, request.request_id)
        
        if not result["success"]:
            # Record error
            game_monitor.record_error(game_id, "action_failed", {
                "player_id": request.player_id,
                "action": request.action,
                "error": result.get("error", "Unknown error")
            })
            raise HTTPException(status_code=400, detail=result.get("error", "Invalid action"))
        
        # Check for validation errors
        if "validation_errors" in result:
            game_monitor.record_error(game_id, "chip_integrity", {
                "errors": result["validation_errors"],
                "action": request.action,
                "player_id": request.player_id
            })
        
        # Broadcast update via WebSocket to all connected players
        await websocket_manager.broadcast_to_game(game_id, {
            "type": "game_update",
            "state": result["state"],
            "animations": result.get("animations", []),
            "last_action": {
                "player_id": request.player_id,
                "action": request.action,
                "amount": request.amount
            },
            "source": "http_action"
        })
        
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
        
        # Process the action (AI actions should also use request IDs to prevent duplicates)
        import uuid
        ai_request_id = f"ai_{request.player_id}_{uuid.uuid4()}"
        result = await game.process_action(request.player_id, action, amount, ai_request_id)
        
        # Broadcast update via WebSocket if action succeeded
        if result.get("success"):
            await websocket_manager.broadcast_to_game(game_id, {
                "type": "game_update",
                "state": result["state"],
                "animations": result.get("animations", []),
                "last_action": {
                    "player_id": request.player_id,
                    "action": action.value,
                    "amount": amount
                },
                "source": "ai_action"
            })
        
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
        from ..core.cache_init import get_cached_calculator
        calculator = get_cached_calculator()
        
        # Count active opponents
        active_opponents = sum(1 for p in game.state.players if p.id != player_id and not p.has_folded)
        
        # If no active opponents, hero has won - no need to calculate
        if active_opponents == 0:
            return {
                "success": True,
                "has_cards": True,
                "win_probability": 1.0,  # 100% win - all opponents folded
                "tie_probability": 0.0,
                "current_hand": "All opponents folded",
                "hand_categories": {},
                "pot_odds": 0,
                "to_call": 0,
                "pot_size": sum(pot.amount for pot in game.state.pots),
                "equity_needed": 0,
                "pot_odds_percentage": 0,
                "has_direct_odds": True
            }
        
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


@router.get("/monitor/metrics")
async def get_monitor_metrics() -> Dict[str, Any]:
    """Get global monitoring metrics"""
    return game_monitor.get_metrics()


@router.get("/monitor/game/{game_id}")
async def get_game_health(game_id: str) -> Dict[str, Any]:
    """Get health status for a specific game"""
    return game_monitor.get_game_health(game_id)


@router.websocket("/ws/{game_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str, player_id: str):
    """WebSocket endpoint for real-time game updates"""
    logger.info(f"WebSocket connection attempt - game_id: {game_id}, player_id: {player_id}")
    
    # Verify game exists
    game = active_games.get(game_id)
    if not game:
        logger.error(f"WebSocket rejected - game {game_id} not found")
        await websocket.close(code=4004, reason="Game not found")
        return
    
    # Verify player exists in game
    player_exists = any(p.id == player_id for p in game.state.players)
    is_spectator = not player_exists
    logger.info(f"Player {player_id} exists: {player_exists}, is_spectator: {is_spectator}")
    
    # Accept WebSocket connection first
    await websocket.accept()
    logger.info(f"WebSocket accepted for {player_id}")
    
    # Connect to WebSocket manager
    try:
        logger.debug(f"Connecting {player_id} to WebSocket manager...")
        conn = await websocket_manager.connect(game_id, player_id, websocket, is_spectator)
        logger.info(f"WebSocket connection established for {player_id}")
        
        # Send initial state
        await conn.send_json({
            "type": "connection_established",
            "game_state": game._serialize_state(),
            "is_spectator": is_spectator
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                # Handle different message types
                if data.get("type") == "ping":
                    await conn.send_json({"type": "pong", "timestamp": data.get("timestamp")})
                    conn.last_ping = time.time()
                
                elif data.get("type") == "action" and not is_spectator:
                    # Process game action via WebSocket
                    action_data = data.get("data", {})
                    try:
                        action = PlayerAction(action_data.get("action"))
                        amount = action_data.get("amount", 0)
                        request_id = action_data.get("request_id")
                        
                        # Record the request
                        is_duplicate = request_id and hasattr(game, '_processed_requests') and request_id in game._processed_requests
                        game_monitor.record_request(game_id, player_id, action_data.get("action"), request_id, is_duplicate)
                        
                        # Process the action
                        result = await game.process_action(player_id, action, amount, request_id)
                        
                        if result["success"]:
                            # Broadcast state update to all players
                            await websocket_manager.broadcast_to_game(game_id, {
                                "type": "game_update",
                                "state": result["state"],
                                "animations": result.get("animations", []),
                                "last_action": {
                                    "player_id": player_id,
                                    "action": action.value,
                                    "amount": amount
                                }
                            })
                        else:
                            # Send error only to the acting player
                            await conn.send_json({
                                "type": "action_error",
                                "error": result.get("error", "Action failed"),
                                "request_id": request_id
                            })
                            
                            # Record error
                            game_monitor.record_error(game_id, "action_failed", {
                                "player_id": player_id,
                                "action": action_data.get("action"),
                                "error": result.get("error")
                            })
                    
                    except ValueError as e:
                        await conn.send_json({
                            "type": "action_error",
                            "error": f"Invalid action: {action_data.get('action')}",
                            "request_id": action_data.get("request_id")
                        })
                
                else:
                    # Unknown message type
                    await conn.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {data.get('type')}"
                    })
            
            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for {player_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message from {player_id}: {e}", exc_info=True)
                await conn.send_json({
                    "type": "error",
                    "error": "Internal server error"
                })
    
    finally:
        # Disconnect from manager
        logger.info(f"Cleaning up WebSocket connection for {player_id}")
        await websocket_manager.disconnect(game_id, player_id)


@router.get("/ws/rooms")
async def get_websocket_rooms() -> Dict[str, Any]:
    """Get information about active WebSocket rooms"""
    return websocket_manager.get_all_rooms_info()