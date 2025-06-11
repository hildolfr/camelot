#!/usr/bin/env python3
"""Test that uncalled bets are properly returned when everyone folds."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.camelot.game.poker_game import PokerGame, PlayerAction

def test_uncalled_bet_return():
    """Test that uncalled bets are returned when everyone folds."""
    print("\n" + "="*60)
    print("Testing uncalled bet return when everyone folds")
    print("="*60)
    
    # Create a game
    config = {
        'players': 2,
        'heroStack': 200,  # 200 BB = $400
        'opponentStacks': [200],  # $400
        'difficulty': 'easy',
        'bigBlind': 2
    }
    
    game = PokerGame(config)
    result = game.start_new_hand()
    
    print(f"\nInitial state:")
    print(f"  Hero stack: ${game.state.players[0].stack}")
    print(f"  Player 2 stack: ${game.state.players[1].stack}")
    print(f"  Current phase: {game.state.phase}")
    
    # Simulate a scenario where Hero goes all-in and opponent folds
    # First, let's see who has the big blind
    hero = game.state.players[0]
    opponent = game.state.players[1]
    
    print(f"\nBlind positions:")
    # In heads-up, dealer is small blind
    if hero.position == game.state.dealer_position:
        print(f"  Hero is small blind (dealer)")
        print(f"  Opponent is big blind")
        hero_is_sb = True
    else:
        print(f"  Hero is big blind")
        print(f"  Opponent is small blind (dealer)")
        hero_is_sb = False
    
    # In heads-up, small blind (dealer) acts first pre-flop
    if hero_is_sb:
        # Hero (SB) goes all-in
        print("\nHero (small blind) going all-in...")
        result = game.process_action(hero.id, PlayerAction.ALL_IN, 0)
        
        print(f"\nAfter Hero all-in:")
        print(f"  Hero stack: ${hero.stack}")
        print(f"  Hero current bet: ${hero.current_bet}")
        print(f"  Pot total: ${sum(pot.amount for pot in game.state.pots) if game.state.pots else 0}")
        
        # Opponent (BB) folds
        print("\nOpponent (big blind) folding to all-in...")
        result = game.process_action(opponent.id, PlayerAction.FOLD, 0)
    else:
        # Wait for opponent to act first, let's have them raise small
        print("\nOpponent (small blind) raises to $10...")
        result = game.process_action(opponent.id, PlayerAction.RAISE, 10)
        
        # Hero (BB) goes all-in 
        print("\nHero (big blind) going all-in...")
        result = game.process_action(hero.id, PlayerAction.ALL_IN, 0)
        
        print(f"\nAfter Hero all-in:")
        print(f"  Hero stack: ${hero.stack}")
        print(f"  Hero current bet: ${hero.current_bet}")
        print(f"  Pot total: ${sum(pot.amount for pot in game.state.pots) if game.state.pots else 0}")
        
        # Opponent folds
        print("\nOpponent folding to all-in...")
        result = game.process_action(opponent.id, PlayerAction.FOLD, 0)
    
    print(f"\nFinal state after hand:")
    print(f"  Hero stack: ${hero.stack}")
    print(f"  Opponent stack: ${opponent.stack}")
    print(f"  Total chips: ${hero.stack + opponent.stack}")
    
    # Verify total chips remain constant
    expected_total = 800  # $400 + $400
    actual_total = hero.stack + opponent.stack
    
    print(f"\nVerification:")
    print(f"  Expected total chips: ${expected_total}")
    print(f"  Actual total chips: ${actual_total}")
    print(f"  Chips {'✓ PRESERVED' if actual_total == expected_total else '✗ LOST!'}")
    
    if actual_total != expected_total:
        print(f"\n⚠️  WARNING: ${expected_total - actual_total} chips missing from the table!")
    else:
        print(f"\n✅ Success: All chips accounted for!")

if __name__ == "__main__":
    test_uncalled_bet_return()