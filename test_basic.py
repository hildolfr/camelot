#!/usr/bin/env python3
"""Basic test to verify Camelot setup."""

import sys
import os

# Add both the project root and poker_knight to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'poker_knight'))

from src.camelot.core.poker_logic import PokerCalculator

def test_poker_knight_integration():
    """Test that poker_knight module works correctly."""
    calculator = PokerCalculator()
    
    # Test a simple calculation
    result = calculator.calculate(
        hero_hand=['A♠', 'K♠'],
        num_opponents=2,
        board_cards=['Q♠', 'J♦', '10♥'],
        simulation_mode='fast'
    )
    
    print("✅ Poker Knight integration successful!")
    print(f"Win probability: {result['win_probability']:.1%}")
    print(f"Simulations run: {result['simulations_run']:,}")
    print(f"Execution time: {result['execution_time_ms']:.1f}ms")

def test_card_validation():
    """Test card validation logic."""
    calculator = PokerCalculator()
    
    # Test valid cards
    assert calculator.validate_card('A♠') == True
    assert calculator.validate_card('10♥') == True
    
    # Test invalid cards
    assert calculator.validate_card('AS') == False
    assert calculator.validate_card('T♥') == False
    
    print("✅ Card validation tests passed!")

if __name__ == "__main__":
    print("🧪 Running basic Camelot tests...")
    print()
    
    try:
        test_card_validation()
        test_poker_knight_integration()
        print()
        print("✅ All tests passed! Camelot is ready to run.")
        print("   Run './run.sh' to start the server.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)