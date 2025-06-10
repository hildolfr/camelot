#!/usr/bin/env python3
"""Test script to verify all-in game flow"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.camelot.game.poker_game import PokerGame, PlayerAction

def test_all_in_scenario():
    """Test a scenario where both players go all-in pre-flop"""
    print("Testing all-in scenario...")
    
    # Create game config
    config = {
        "players": 2,
        "heroStack": 200,
        "opponentStacks": [200],
        "difficulty": "easy",
        "bigBlind": 2
    }
    
    # Create game
    game = PokerGame(config)
    
    # Start new hand
    result = game.start_new_hand()
    print(f"New hand started: {result['success']}")
    print(f"Phase: {game.state.phase.name}")
    print(f"Action on: {game.state.action_on}")
    
    # Find who acts first
    acting_player = game.state.players[game.state.action_on] if game.state.action_on >= 0 else None
    if not acting_player:
        print("ERROR: No player to act!")
        return
    
    print(f"\nFirst to act: {acting_player.name}")
    
    # If AI acts first, let them act
    if acting_player.is_ai:
        # For testing, make AI go all-in
        result = game.process_action(acting_player.id, PlayerAction.ALL_IN)
        print(f"AI went all-in: {result['success']}")
        print(f"Phase after AI all-in: {game.state.phase.name}")
        print(f"Action on: {game.state.action_on}")
        
        # Now hero responds with all-in
        if game.state.action_on >= 0:
            hero = game.state.players[game.state.action_on]
            result = game.process_action(hero.id, PlayerAction.ALL_IN)
            print(f"\nHero went all-in: {result['success']}")
        else:
            print("ERROR: No one to act after AI all-in!")
            
    else:
        # Hero acts first - go all-in
        result = game.process_action("hero", PlayerAction.ALL_IN)
        print(f"Hero went all-in: {result['success']}")
        print(f"Phase after hero all-in: {game.state.phase.name}")
        print(f"Action on: {game.state.action_on}")
        
        # Now AI responds
        if game.state.action_on >= 0:
            ai = game.state.players[game.state.action_on]
            result = game.process_action(ai.id, PlayerAction.ALL_IN)
            print(f"\nAI went all-in: {result['success']}")
        else:
            print("ERROR: No one to act after hero all-in!")
    
    # Check final state
    print(f"\nFinal phase: {game.state.phase.name}")
    print(f"Board cards: {game.state.board_cards}")
    print(f"Action on: {game.state.action_on}")
    
    # Check if game properly advanced through all phases
    if game.state.phase.name == "SHOWDOWN" or game.state.phase.name == "GAME_OVER":
        print("\nSUCCESS: Game properly advanced to showdown when all players are all-in!")
        print(f"Total board cards dealt: {len(game.state.board_cards)}")
    else:
        print(f"\nERROR: Game stalled at phase {game.state.phase.name} with {len(game.state.board_cards)} board cards")
        print(f"Action on: {game.state.action_on}")
        
    # Print animation queue to see if phases were queued
    if result.get('animations'):
        print(f"\nAnimations queued: {len(result['animations'])}")
        for anim in result['animations']:
            print(f"  - {anim['type']}: {anim.get('card', anim.get('message', ''))}")

if __name__ == "__main__":
    test_all_in_scenario()