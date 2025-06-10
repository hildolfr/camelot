#!/usr/bin/env python3
"""Test script to verify raise validation logic."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from camelot.game.poker_game import PokerGame, PlayerAction, GamePhase
from camelot.game.ai_player import AIPlayer

def test_raise_validation():
    """Test that AI never raises less than a player's previous raise."""
    print("Testing raise validation logic...")
    
    # Create a game with 2 players
    config = {
        'heroStack': 100,  # 100 BB
        'opponentStacks': [100],  # 1 opponent with 100 BB
        'bigBlind': 10
    }
    
    game = PokerGame(config)
    ai = AIPlayer("medium")
    
    # Start a new hand
    result = game.start_new_hand()
    print(f"Hand started. Small blind: {game.state.small_blind}, Big blind: {game.state.big_blind}")
    
    # Get initial state
    print(f"\nInitial state:")
    print(f"  Current bet: {game.state.current_bet}")
    print(f"  Min raise: {game.state.min_raise}")
    print(f"  Action on: Player {game.state.action_on}")
    
    # Find who's first to act
    hero = game.state.players[0]
    ai_player = game.state.players[1]
    
    print(f"\nPlayers:")
    print(f"  Hero: position={hero.position}, stack={hero.stack}, current_bet={hero.current_bet}, is_sb={hero.position == game._get_small_blind_position()}, is_bb={hero.position == game._get_big_blind_position()}")
    print(f"  AI: position={ai_player.position}, stack={ai_player.stack}, current_bet={ai_player.current_bet}, is_sb={ai_player.position == game._get_small_blind_position()}, is_bb={ai_player.position == game._get_big_blind_position()}")
    
    # Check who should act first
    acting_player_id = game.state.players[game.state.action_on].id if game.state.action_on >= 0 else None
    print(f"\nFirst to act: {acting_player_id}")
    
    # If AI acts first, let it act then test hero's raise
    if acting_player_id == "ai_1":
        print(f"\n=== AI ACTS FIRST ===")
        ai_action, ai_amount = ai.decide_action(game.state, ai_player)
        print(f"AI decision: {ai_action.value} with amount {ai_amount}")
        result = game.process_action(ai_player.id, ai_action, ai_amount)
        if not result["success"]:
            print(f"ERROR: AI action failed: {result.get('error')}")
            return
        print(f"AI action successful. Current bet now: {game.state.current_bet}")
    
    # Now hero raises
    print(f"\n=== HERO RAISES by 30 (to {game.state.current_bet + 30} total) ===")
    result = game.process_action("hero", PlayerAction.RAISE, 30)
    if not result["success"]:
        print(f"ERROR: Hero raise failed: {result.get('error')}")
        return
    
    print(f"After hero raise:")
    print(f"  Current bet: {game.state.current_bet}")
    print(f"  Min raise: {game.state.min_raise}")
    print(f"  Hero bet: {hero.current_bet}")
    
    # Now it's AI's turn - let AI decide
    print(f"\n=== AI's TURN ===")
    ai_action, ai_amount = ai.decide_action(game.state, ai_player)
    print(f"AI decision: {ai_action.value} with amount {ai_amount}")
    
    if ai_action == PlayerAction.RAISE:
        print(f"AI wants to raise by {ai_amount}")
        print(f"This would make total bet: {game.state.current_bet + ai_amount}")
        print(f"Minimum allowed raise: {game.state.min_raise}")
        
        if ai_amount < game.state.min_raise:
            print(f"ERROR: AI tried to raise by {ai_amount} but minimum is {game.state.min_raise}!")
        else:
            print(f"OK: AI raise amount {ai_amount} >= minimum {game.state.min_raise}")
    
    # Process AI action
    result = game.process_action(ai_player.id, ai_action, ai_amount)
    if not result["success"]:
        print(f"ERROR: AI action failed: {result.get('error')}")
    else:
        print(f"AI action successful")
        print(f"After AI action:")
        print(f"  Current bet: {game.state.current_bet}")
        print(f"  Min raise: {game.state.min_raise}")
        print(f"  AI bet: {ai_player.current_bet}")
        
        if ai_action == PlayerAction.RAISE and ai_player.current_bet <= hero.current_bet:
            print(f"ERROR: AI raised but total bet ({ai_player.current_bet}) <= hero's bet ({hero.current_bet})!")

if __name__ == "__main__":
    test_raise_validation()