#!/usr/bin/env python3
"""Demo script showing hand evaluation in action."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from camelot.core.hand_evaluator import get_winning_players


def demo_showdown():
    """Demonstrate a showdown with various hands."""
    print("=" * 60)
    print("Texas Hold'em Showdown Demo")
    print("=" * 60)
    
    # Board: A♠ K♦ Q♣ J♥ 5♠
    board = ['A♠', 'K♦', 'Q♣', 'J♥', '5♠']
    print(f"\nBoard: {' '.join(board)}")
    print("-" * 40)
    
    # Players with different hands
    players = {
        'Hero': ['T♠', '9♠'],      # Straight (not broadway)
        'Villain1': ['A♥', 'A♣'],  # Three of a kind (aces)
        'Villain2': ['K♥', 'K♣'],  # Three of a kind (kings)
        'Villain3': ['T♥', '8♦'],  # Straight (ace high)
        'Villain4': ['5♥', '5♦'],  # Three of a kind (fives)
    }
    
    print("\nPlayer Hands:")
    for player, cards in players.items():
        print(f"  {player}: {cards[0]} {cards[1]}")
    
    # Determine winners
    winners, evaluations = get_winning_players(players, board)
    
    print("\nHand Evaluations:")
    for player, eval in evaluations.items():
        cards = players[player]
        print(f"  {player} ({cards[0]} {cards[1]}): {eval}")
    
    print(f"\n🏆 Winner(s): {', '.join(winners)}")
    
    # Another example - split pot
    print("\n" + "=" * 60)
    print("Split Pot Example")
    print("=" * 60)
    
    board2 = ['A♠', 'K♦', 'Q♣', 'J♥', 'T♠']  # Broadway on board
    print(f"\nBoard: {' '.join(board2)}")
    print("-" * 40)
    
    players2 = {
        'Player1': ['9♥', '8♦'],  # Straight (king high)
        'Player2': ['7♣', '6♣'],  # Board plays
        'Player3': ['2♦', '3♦'],  # Board plays
    }
    
    print("\nPlayer Hands:")
    for player, cards in players2.items():
        print(f"  {player}: {cards[0]} {cards[1]}")
    
    winners2, evaluations2 = get_winning_players(players2, board2)
    
    print("\nHand Evaluations:")
    for player, eval in evaluations2.items():
        cards = players2[player]
        print(f"  {player} ({cards[0]} {cards[1]}): {eval}")
    
    print(f"\n🏆 Winner(s): {', '.join(winners2)} (Split Pot!)")
    
    # Flush vs Full House example
    print("\n" + "=" * 60)
    print("Flush vs Full House")
    print("=" * 60)
    
    board3 = ['K♥', 'K♦', '7♥', '3♥', '2♥']
    print(f"\nBoard: {' '.join(board3)}")
    print("-" * 40)
    
    players3 = {
        'FlushPlayer': ['A♥', '9♥'],   # Ace-high flush
        'FullHousePlayer': ['K♣', '7♣'], # Kings full of sevens
        'TwoPairPlayer': ['7♦', '3♦'],   # Two pair (kings and sevens)
    }
    
    print("\nPlayer Hands:")
    for player, cards in players3.items():
        print(f"  {player}: {cards[0]} {cards[1]}")
    
    winners3, evaluations3 = get_winning_players(players3, board3)
    
    print("\nHand Evaluations:")
    for player, eval in evaluations3.items():
        cards = players3[player]
        print(f"  {player} ({cards[0]} {cards[1]}): {eval}")
    
    print(f"\n🏆 Winner(s): {', '.join(winners3)}")


if __name__ == "__main__":
    demo_showdown()