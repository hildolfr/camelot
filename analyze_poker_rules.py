#!/usr/bin/env python3
"""
Texas Hold'em Rules Analyzer
This script defines the correct rules and flow of Texas Hold'em poker
to help identify violations in the current implementation.
"""

print("""
TEXAS HOLD'EM POKER - CORRECT GAME FLOW AND RULES
==================================================

1. HAND SETUP:
   - Dealer button moves clockwise
   - Small blind posts (left of dealer, or dealer in heads-up)
   - Big blind posts (left of small blind)
   - Each player dealt 2 hole cards
   - First to act: left of big blind (pre-flop)

2. BETTING ROUNDS:
   
   A. PRE-FLOP:
      - Action starts left of big blind
      - Players can: FOLD, CALL (match big blind), or RAISE
      - Big blind has option to raise even if everyone just calls
      - Round ends when all active players have matched the highest bet
   
   B. FLOP (3 community cards):
      - Betting resets to $0
      - Action starts left of dealer (first active player)
      - Players can: CHECK (if no bet), BET, CALL, RAISE, or FOLD
      - Round ends when all active players have matched the highest bet
   
   C. TURN (4th community card):
      - Same as flop
   
   D. RIVER (5th community card):
      - Same as flop
   
   E. SHOWDOWN:
      - If multiple players remain, best hand wins
      - If only one player remains (others folded), they win

3. CRITICAL RULES:
   
   ✓ NO player can CHECK when facing a bet - they must CALL, RAISE, or FOLD
   ✓ A betting round ONLY completes when ALL active players have:
     - Matched the current highest bet, OR
     - Gone all-in with their remaining chips, OR
     - Folded
   
   ✓ When someone raises:
     - ALL other players must act again (even if they already acted)
     - The betting round essentially "restarts" at the raiser
   
   ✓ Going all-in:
     - If a player doesn't have enough to call, they go all-in
     - This creates a side pot for remaining players
     - All-in player can only win up to what they contributed
   
   ✓ Phase transitions:
     - Can ONLY happen after betting round completes
     - All bets reset to $0 for new betting round
     - Board cards are dealt for the new phase

4. COMMON VIOLATIONS TO CHECK:
   
   ❌ Allowing CHECK when facing a bet
   ❌ Advancing phases before all players respond to raises
   ❌ Not giving all players a chance to act after a raise
   ❌ Dealing community cards while betting is active
   ❌ Allowing players to act out of turn
   ❌ Not resetting bets between betting rounds
   ❌ Skipping players who need to respond to bets

5. EXAMPLE SCENARIO - CORRECT FLOW:
   
   Turn betting:
   - Player A: CHECK
   - Player B: BET $50
   - Player C: RAISE to $150
   - Player A: Must act again! (CALL $150, RERAISE, or FOLD)
   - Player B: Must act again! (CALL additional $100, RERAISE, or FOLD)
   - Only after A and B respond can we move to river

6. EXAMPLE SCENARIO - ALL-IN:
   
   Pre-flop:
   - Small blind: $1
   - Big blind: $2
   - Player C: RAISE to $10
   - Player D: ALL-IN $100
   - Small blind: Must respond to $100 (CALL, ALL-IN, or FOLD)
   - Big blind: Must respond to $100 (CALL, ALL-IN, or FOLD)
   - Player C: Must respond to $100 (CALL additional $90, RERAISE, or FOLD)
""")

# Key validation functions that should exist
def validate_action(game_state, player, action):
    """Check if an action is valid given the game state"""
    
    # Rule 1: Cannot CHECK when facing a bet
    if action == "CHECK" and game_state.current_bet > player.current_bet:
        return False, "Cannot CHECK when facing a bet"
    
    # Rule 2: CALL must match the bet (or go all-in trying)
    if action == "CALL":
        to_call = game_state.current_bet - player.current_bet
        if to_call > player.stack:
            return False, "Should be ALL_IN, not CALL"
    
    return True, "Valid"

def is_betting_round_complete(game_state):
    """Check if betting round is truly complete"""
    
    active_players = [p for p in game_state.players if not p.has_folded and p.stack > 0]
    
    # All active players must have:
    # 1. Acted at least once (last_action != None)
    # 2. Matched the current bet OR be all-in
    
    for player in active_players:
        # Player hasn't acted yet
        if player.last_action is None:
            return False, f"{player.name} hasn't acted yet"
        
        # Player hasn't matched the bet and has chips
        if player.current_bet < game_state.current_bet and player.stack > 0:
            return False, f"{player.name} needs to match bet"
    
    return True, "All players have acted and matched"

print("\nTo analyze game logs, look for:")
print("1. CHECK actions when current_bet > player.current_bet")
print("2. Phase transitions when players haven't matched bets")
print("3. Players not getting a chance to respond to raises")
print("4. Betting rounds completing prematurely")