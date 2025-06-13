#!/usr/bin/env python3
"""Test hand evaluation functionality."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from camelot.core.hand_evaluator import (
    evaluate_hand, get_winning_players, HandRank, Card
)


def test_basic_hands():
    """Test basic hand evaluations."""
    print("Testing basic hand evaluations...")
    
    # Test Royal Flush
    hole = ['A♠', 'K♠']
    board = ['Q♠', 'J♠', 'T♠', '5♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Royal Flush: {result}")
    assert result.rank == HandRank.ROYAL_FLUSH
    
    # Test Straight Flush
    hole = ['9♥', '8♥']
    board = ['7♥', '6♥', '5♥', 'K♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Straight Flush: {result}")
    assert result.rank == HandRank.STRAIGHT_FLUSH
    
    # Test Four of a Kind
    hole = ['A♠', 'A♥']
    board = ['A♦', 'A♣', 'K♠', 'Q♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Four of a Kind: {result}")
    assert result.rank == HandRank.FOUR_OF_A_KIND
    
    # Test Full House
    hole = ['K♠', 'K♥']
    board = ['K♦', 'Q♣', 'Q♠', '7♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Full House: {result}")
    assert result.rank == HandRank.FULL_HOUSE
    
    # Test Flush
    hole = ['A♣', '9♣']
    board = ['K♣', '7♣', '3♣', 'J♦', '2♠']
    result = evaluate_hand(hole, board)
    print(f"Flush: {result}")
    assert result.rank == HandRank.FLUSH
    
    # Test Straight
    hole = ['9♠', '8♦']
    board = ['7♣', '6♥', '5♠', 'K♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Straight: {result}")
    assert result.rank == HandRank.STRAIGHT
    
    # Test Three of a Kind
    hole = ['J♠', 'J♥']
    board = ['J♦', 'Q♣', '8♠', '7♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Three of a Kind: {result}")
    assert result.rank == HandRank.THREE_OF_A_KIND
    
    # Test Two Pair
    hole = ['K♠', 'K♥']
    board = ['Q♦', 'Q♣', '8♠', '7♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Two Pair: {result}")
    assert result.rank == HandRank.TWO_PAIR
    
    # Test One Pair
    hole = ['A♠', 'K♥']
    board = ['A♦', 'Q♣', '8♠', '7♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"One Pair: {result}")
    assert result.rank == HandRank.ONE_PAIR
    
    # Test High Card
    hole = ['A♠', 'K♥']
    board = ['Q♦', 'J♣', '9♠', '7♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"High Card: {result}")
    assert result.rank == HandRank.HIGH_CARD
    
    print("✓ All basic hand tests passed!\n")


def test_winner_determination():
    """Test determining winners in various scenarios."""
    print("Testing winner determination...")
    
    board = ['K♠', 'Q♦', 'J♣', '5♥', '2♠']
    
    # Test 1: Clear winner
    players = {
        'p1': ['A♠', 'T♠'],  # Straight (ace high)
        'p2': ['K♥', 'K♣'],  # Three of a kind
        'p3': ['Q♥', 'Q♣']   # Three of a kind (lower)
    }
    winners, evals = get_winning_players(players, board)
    print(f"Test 1 - Clear winner:")
    for pid, eval in evals.items():
        print(f"  {pid}: {eval}")
    print(f"  Winners: {winners}")
    assert winners == ['p1']
    
    # Test 2: Tie (split pot)
    board2 = ['A♠', 'K♦', 'Q♣', 'J♥', 'T♠']  # Board has straight
    players2 = {
        'p1': ['9♠', '8♠'],  # Straight (lower)
        'p2': ['7♥', '6♣'],  # Straight (lower)
        'p3': ['2♦', '3♦']   # Straight (board plays)
    }
    winners2, evals2 = get_winning_players(players2, board2)
    print(f"\nTest 2 - Tie scenario:")
    for pid, eval in evals2.items():
        print(f"  {pid}: {eval}")
    print(f"  Winners: {winners2}")
    # All players have ace-high straight from board
    assert len(winners2) == 3
    
    # Test 3: Kicker matters
    board3 = ['K♠', 'K♦', '7♣', '5♥', '2♠']
    players3 = {
        'p1': ['A♠', 'Q♠'],  # Pair of kings, ace kicker
        'p2': ['A♥', 'J♣'],  # Pair of kings, ace-jack kicker  
        'p3': ['Q♦', 'J♦']   # Pair of kings, queen kicker
    }
    winners3, evals3 = get_winning_players(players3, board3)
    print(f"\nTest 3 - Kicker test:")
    for pid, eval in evals3.items():
        print(f"  {pid}: {eval}")
    print(f"  Winners: {winners3}")
    assert winners3 == ['p1']
    
    print("✓ All winner determination tests passed!\n")


def test_special_cases():
    """Test special cases like wheel straight."""
    print("Testing special cases...")
    
    # Test wheel (A-2-3-4-5 straight)
    hole = ['A♠', '4♥']
    board = ['5♦', '3♣', '2♠', 'K♦', 'J♣']
    result = evaluate_hand(hole, board)
    print(f"Wheel straight: {result}")
    assert result.rank == HandRank.STRAIGHT
    assert result.value == (5,)  # 5-high straight
    
    # Test that 10 is handled correctly
    hole = ['10♠', '10♥']
    board = ['10♦', 'Q♣', '8♠', '7♦', '2♣']
    result = evaluate_hand(hole, board)
    print(f"Three tens: {result}")
    assert result.rank == HandRank.THREE_OF_A_KIND
    
    print("✓ All special case tests passed!\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Hand Evaluator Test Suite")
    print("=" * 60)
    print()
    
    test_basic_hands()
    test_winner_determination()
    test_special_cases()
    
    print("=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)