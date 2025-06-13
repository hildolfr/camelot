#!/usr/bin/env python3
"""Integration test for poker game with hand evaluation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from camelot.game.poker_game import PokerGame, GamePhase, PlayerAction
from camelot.game.ai_player import AIPlayer
import json


def test_game_with_showdown():
    """Test a complete game through showdown to verify hand evaluation works."""
    print("Testing poker game with showdown...")
    
    # Create a game with 3 players
    config = {
        'players': 3,
        'heroStack': 100,  # 100 BB
        'opponentStacks': [100, 100],  # Two AI opponents with 100 BB each
        'difficulty': 'normal',
        'bigBlind': 10
    }
    
    game = PokerGame(config)
    print(f"Created game with ID: {game.game_id}")
    
    # Start a new hand
    result = game.start_new_hand()
    print(f"Started new hand #{game.state.hand_number}")
    
    # Get initial state
    state = game._serialize_state()
    print(f"Initial phase: {state['phase']}")
    print(f"Players: {len(state['players'])}")
    
    # Simulate a hand where we go to showdown
    # We'll have hero call/check through to showdown
    
    # Pre-flop: Hero is likely in position 0, 1, or 2 depending on dealer
    # Let's process actions until we get to hero
    while game.state.phase == GamePhase.PRE_FLOP:
        current_player = game.state.players[game.state.action_on]
        
        if current_player.id == "hero":
            # Hero calls/checks
            if game.state.current_bet > current_player.current_bet:
                result = game.process_action("hero", PlayerAction.CALL, 0)
            else:
                result = game.process_action("hero", PlayerAction.CHECK, 0)
            print(f"Hero action: {result.get('last_action', {}).get('action')}")
        else:
            # Process AI action
            ai = AIPlayer(config.get('difficulty', 'normal'))
            action, amount = ai.decide_action(game.state, current_player)
            result = game.process_action(current_player.id, action, amount)
            print(f"{current_player.name} action: {result.get('last_action', {}).get('action')}")
        
        if not result['success']:
            print(f"Action failed: {result}")
            break
    
    # Continue through flop, turn, river
    for phase_name in ['FLOP', 'TURN', 'RIVER']:
        print(f"\n{phase_name}:")
        state = game._serialize_state()
        print(f"Board: {state['board_cards']}")
        
        while game.state.phase.name == phase_name:
            current_player = game.state.players[game.state.action_on]
            
            if current_player.id == "hero":
                # Hero checks/calls
                if game.state.current_bet > current_player.current_bet:
                    result = game.process_action("hero", PlayerAction.CALL, 0)
                else:
                    result = game.process_action("hero", PlayerAction.CHECK, 0)
                print(f"Hero action: {result.get('last_action', {}).get('action')}")
            else:
                # Process AI action
                ai = AIPlayer(config.get('difficulty', 'normal'))
                action, amount = ai.decide_action(game.state, current_player)
                result = game.process_action(current_player.id, action, amount)
                print(f"{current_player.name} action: {result.get('last_action', {}).get('action')}")
            
            if not result['success']:
                print(f"Action failed: {result}")
                break
    
    # Check if we reached showdown
    final_state = game._serialize_state()
    print(f"\nFinal phase: {final_state['phase']}")
    
    if final_state['phase'] == 'game_over':
        print("\nGame reached showdown!")
        
        # Check the last animations for pot awards
        if 'animations' in result:
            for anim in result['animations']:
                if anim['type'] == 'award_pot':
                    winner_id = anim['winner_id']
                    amount = anim['amount']
                    hand_name = anim.get('hand_name', 'Unknown')
                    print(f"Pot awarded to {winner_id}: ${amount} with {hand_name}")
    
    print("\n✓ Integration test completed!")
    return game


def test_player_limit_validation():
    """Test that player count validation works."""
    print("\nTesting player count validation...")
    
    # Test too many players
    try:
        config = {
            'players': 11,  # 1 hero + 10 AI = 11 total (exceeds limit)
            'heroStack': 100,
            'opponentStacks': [100] * 10,
            'difficulty': 'normal',
            'bigBlind': 10
        }
        game = PokerGame(config)
        print("ERROR: Should have raised exception for 11 players!")
    except ValueError as e:
        print(f"✓ Correctly rejected 11 players: {e}")
    
    # Test valid player count
    try:
        config = {
            'players': 10,  # 1 hero + 9 AI = 10 total (at limit)
            'heroStack': 100,
            'opponentStacks': [100] * 9,
            'difficulty': 'normal',
            'bigBlind': 10
        }
        game = PokerGame(config)
        print("✓ Correctly accepted 10 players")
    except ValueError as e:
        print(f"ERROR: Should have accepted 10 players: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Poker Game Integration Test")
    print("=" * 60)
    print()
    
    # Test full game
    game = test_game_with_showdown()
    
    # Test validation
    test_player_limit_validation()
    
    print("\n" + "=" * 60)
    print("✅ INTEGRATION TESTS COMPLETED!")
    print("=" * 60)