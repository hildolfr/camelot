#!/usr/bin/env python3
"""Comprehensive test of raise validation scenarios."""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from camelot.game.poker_game import PokerGame, PlayerAction, GamePhase
from camelot.game.ai_player import AIPlayer

def test_multiple_raises():
    """Test multiple raises in a row to ensure min raise is properly tracked."""
    print("Testing multiple raises scenario...")
    
    # Create a game with 3 players
    config = {
        'heroStack': 200,  # 200 BB
        'opponentStacks': [200, 200],  # 2 opponents with 200 BB each
        'bigBlind': 10
    }
    
    game = PokerGame(config)
    ai = AIPlayer("hard")  # Use hard AI for more aggressive play
    
    # Start a new hand
    result = game.start_new_hand()
    print(f"Hand started. Players: {len(game.state.players)}")
    
    # Identify positions
    for i, player in enumerate(game.state.players):
        is_sb = player.position == game._get_small_blind_position()
        is_bb = player.position == game._get_big_blind_position()
        print(f"  {player.id}: position={player.position}, stack={player.stack}, bet={player.current_bet}, SB={is_sb}, BB={is_bb}")
    
    print(f"\nInitial: current_bet={game.state.current_bet}, min_raise={game.state.min_raise}")
    
    # Process actions until we see multiple raises
    action_count = 0
    raise_history = []
    
    while game.state.phase == GamePhase.PRE_FLOP and action_count < 10:
        acting_player = game.state.players[game.state.action_on]
        print(f"\n--- Action {action_count + 1}: {acting_player.id}'s turn ---")
        print(f"Current bet: {game.state.current_bet}, Min raise: {game.state.min_raise}")
        print(f"{acting_player.id} has bet: {acting_player.current_bet}, needs: {game.state.current_bet - acting_player.current_bet}")
        
        if acting_player.id == "hero":
            # Hero always raises aggressively for this test
            if game.state.current_bet > acting_player.current_bet:
                # Must at least call
                to_call = game.state.current_bet - acting_player.current_bet
                if acting_player.stack > to_call + game.state.min_raise:
                    # Can raise
                    raise_amount = game.state.min_raise * 2  # Raise double the minimum
                    action = PlayerAction.RAISE
                    print(f"Hero raises by {raise_amount}")
                else:
                    # Just call
                    action = PlayerAction.CALL
                    raise_amount = 0
                    print(f"Hero calls")
            else:
                # Can check or raise
                if acting_player.stack > game.state.min_raise:
                    raise_amount = game.state.min_raise * 2
                    action = PlayerAction.RAISE
                    print(f"Hero raises by {raise_amount}")
                else:
                    action = PlayerAction.CHECK
                    raise_amount = 0
                    print(f"Hero checks")
            
            result = game.process_action("hero", action, raise_amount)
        else:
            # AI player
            ai_player = acting_player
            action, amount = ai.decide_action(game.state, ai_player)
            print(f"{ai_player.id} decides: {action.value} with amount {amount}")
            
            if action == PlayerAction.RAISE:
                raise_history.append({
                    'player': ai_player.id,
                    'raise_amount': amount,
                    'min_raise': game.state.min_raise,
                    'current_bet_before': game.state.current_bet,
                    'player_bet_before': ai_player.current_bet
                })
                
                # Validate raise
                if amount < game.state.min_raise:
                    print(f"ERROR: {ai_player.id} tried to raise {amount} but minimum is {game.state.min_raise}!")
            
            result = game.process_action(ai_player.id, action, amount)
        
        if not result["success"]:
            print(f"ERROR: Action failed: {result.get('error')}")
            break
        
        print(f"After action: current_bet={game.state.current_bet}, min_raise={game.state.min_raise}")
        
        action_count += 1
        
        # Check if betting round is complete
        if game.state.phase != GamePhase.PRE_FLOP:
            print("\nBetting round complete, moving to next phase")
            break
    
    # Analyze raise history
    print(f"\n=== RAISE HISTORY ANALYSIS ===")
    print(f"Total raises: {len(raise_history)}")
    for i, raise_info in enumerate(raise_history):
        print(f"\nRaise {i + 1}:")
        print(f"  Player: {raise_info['player']}")
        print(f"  Min raise required: {raise_info['min_raise']}")
        print(f"  Actual raise amount: {raise_info['raise_amount']}")
        print(f"  Valid: {'YES' if raise_info['raise_amount'] >= raise_info['min_raise'] else 'NO'}")
        print(f"  Bet increased from {raise_info['current_bet_before']} to {raise_info['current_bet_before'] + raise_info['raise_amount']}")
    
    # Check for any invalid raises
    invalid_raises = [r for r in raise_history if r['raise_amount'] < r['min_raise']]
    if invalid_raises:
        print(f"\nERROR: Found {len(invalid_raises)} invalid raises!")
        for r in invalid_raises:
            print(f"  {r['player']} raised {r['raise_amount']} when minimum was {r['min_raise']}")
    else:
        print(f"\nSUCCESS: All {len(raise_history)} raises were valid!")

def test_small_stack_scenario():
    """Test scenario where AI has a small stack and can't meet minimum raise."""
    print("\n\n=== TESTING SMALL STACK SCENARIO ===")
    
    config = {
        'heroStack': 100,
        'opponentStacks': [15],  # AI has only 15 BB
        'bigBlind': 10
    }
    
    game = PokerGame(config)
    ai = AIPlayer("medium")
    
    # Start hand
    game.start_new_hand()
    
    # Make hero raise big
    if game.state.action_on == 0:  # Hero acts first
        print("Hero raises to 50")
        result = game.process_action("hero", PlayerAction.RAISE, 40)  # Raise to 50 total
        if result["success"]:
            print(f"Current bet: {game.state.current_bet}, Min raise: {game.state.min_raise}")
            
            # Now AI must act
            ai_player = game.state.players[1]
            print(f"\nAI has stack: {ai_player.stack}, current bet: {ai_player.current_bet}")
            print(f"To call: {game.state.current_bet - ai_player.current_bet}")
            print(f"After calling, would have: {ai_player.stack - (game.state.current_bet - ai_player.current_bet)}")
            
            action, amount = ai.decide_action(game.state, ai_player)
            print(f"AI decision: {action.value} with amount {amount}")
            
            if action == PlayerAction.RAISE:
                print("ERROR: AI shouldn't be able to raise with such a small stack!")
            elif action == PlayerAction.ALL_IN:
                print("CORRECT: AI goes all-in since it can't meet minimum raise")
            elif action == PlayerAction.CALL:
                remaining = ai_player.stack - (game.state.current_bet - ai_player.current_bet)
                if remaining < game.state.min_raise:
                    print(f"OK: AI calls, leaving {remaining} chips (less than min raise {game.state.min_raise})")

if __name__ == "__main__":
    test_multiple_raises()
    test_small_stack_scenario()