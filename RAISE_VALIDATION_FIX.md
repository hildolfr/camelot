# Raise Validation Fix Summary

## Bug Description
The user reported that the AI sometimes raised less than the player did, which is an illegal move in poker. The minimum raise must be at least as much as the previous raise.

## Root Cause
1. The `min_raise` tracking was correct in `poker_game.py`, but it was being set to just the raise amount, not ensuring it was at least as large as the previous minimum.
2. The AI's `_calculate_raise_amount()` method didn't properly validate that it could actually make the minimum raise with its remaining stack.
3. The AI would sometimes attempt to raise when it couldn't meet the minimum, leading to invalid actions.

## Changes Made

### 1. Fixed min_raise tracking in poker_game.py
- Changed line 454 from `self.state.min_raise = amount` to `self.state.min_raise = max(amount, self.state.min_raise)`
- This ensures the minimum raise can only increase, never decrease
- Added detailed logging for raise validation

### 2. Improved AI raise calculation in ai_player.py
- Updated `_calculate_raise_amount()` to:
  - Include current bets in pot size calculation for better decision making
  - Check if the AI can actually afford the minimum raise
  - Return 0 if unable to make a valid raise (signal to caller)
  - Add comprehensive logging

### 3. Updated AI decision logic
- Modified all raise decision points to check if `raise_amount > 0` before attempting to raise
- If the AI wants to raise but can't meet the minimum, it will call or check instead
- This prevents the AI from making invalid raise attempts

### 4. Test Scripts Created
- `test_raise_validation.py`: Basic test of raise validation
- `test_comprehensive_raises.py`: More thorough testing including multiple raises and small stack scenarios

## Testing Results
The fix has been tested and verified to work correctly:
- AI now always raises by at least the minimum required amount
- When AI can't afford the minimum raise, it correctly calls or goes all-in instead
- The minimum raise is properly tracked across multiple raises in a betting round

## Poker Rules Enforced
1. A raise must be at least the size of the previous bet or raise in the same round
2. If a player cannot meet the minimum raise requirement, they cannot raise (must call, fold, or go all-in)
3. The minimum raise is reset to the big blind amount at the start of each new betting round (flop, turn, river)