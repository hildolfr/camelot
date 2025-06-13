TEXAS HOLD'EM POKER GAME LOGIC IMPLEMENTATION NOTES

---

1. PLAYERS
- Game supports 2 to 10 players per table.
- Each player has:
  - Unique seat ID
  - Chip stack (integer value)
  - Two private hole cards
  - Status: ACTIVE, FOLDED, ALL_IN, BUSTED

---

2. DEALER BUTTON & BLINDS
- Dealer button rotates clockwise each hand.
- Small Blind (SB) is posted by player left of dealer.
- Big Blind (BB) is posted by player left of SB.
- SB = 0.5 * BB
- Dealer, SB, and BB move each round.

---

3. HAND PHASES

Phase A: PRE-FLOP
- Deal 2 private (hole) cards to each ACTIVE player.
- Betting begins with player left of BB (Under the Gun).
- Actions: FOLD, CALL, RAISE, CHECK (only if no bet faced).

Phase B: FLOP
- Burn 1 card.
- Reveal 3 community cards face-up.
- Betting begins with first ACTIVE player left of dealer.

Phase C: TURN
- Burn 1 card.
- Reveal 4th community card.
- Betting begins with first ACTIVE player left of dealer.

Phase D: RIVER
- Burn 1 card.
- Reveal 5th and final community card.
- Betting begins with first ACTIVE player left of dealer.

Phase E: SHOWDOWN
- If 2+ players remain:
  - All reveal hole cards.
  - Evaluate best 5-card hand using hole + community cards.
  - Determine winner(s).
  - Distribute main pot and side pots if necessary.
- If only 1 player remains after betting, no showdown occurs; that player wins the pot.

---

4. BETTING RULES
- Default structure: NO LIMIT
  - Players may bet any amount >= current minimum raise up to their total chip stack.
- Betting proceeds clockwise.
- Actions:
  - FOLD: player exits current hand.
  - CALL: match highest current bet.
  - RAISE: increase current bet by at least the previous raise amount.
  - CHECK: pass turn if no bet to match.

---

5. POT & SIDE POT MANAGEMENT
- If player goes ALL-IN for less than the current bet:
  - Create SIDE POT.
  - Only players who match full amount can win from side pot.
  - Each pot tracks eligible players.
- At showdown:
  - Evaluate hands and distribute pots in sequence.

---

6. HAND EVALUATION
- Use 7 cards (2 hole + 5 community) to make best 5-card hand.
- Ranking (highest to lowest):
  1. Royal Flush (A-K-Q-J-10 same suit)
  2. Straight Flush (5 sequential cards same suit)
  3. Four of a Kind (4 same rank)
  4. Full House (3 of a kind + pair)
  5. Flush (5 same suit, any order)
  6. Straight (5 sequential, any suit)
  7. Three of a Kind
  8. Two Pair
  9. One Pair
  10. High Card (none of above)
- Tie-breakers determined by kicker cards.

---

7. GAME LOOP (PSEUDOCODE)

```
while number_of_players > 1:
    assignDealerButton()
    postSmallBlind()
    postBigBlind()
    dealHoleCards()

    bettingRound(start=UTG)

    dealFlop()
    bettingRound(start=leftOfDealer)

    dealTurn()
    bettingRound(start=leftOfDealer)

    dealRiver()
    bettingRound(start=leftOfDealer)

    if more than one player remains:
        showdown()
        evaluateHands()
        distributePots()
    else:
        awardPotToLastPlayer()

    eliminateBustedPlayers()
    rotateDealerButton()
```

---

8. WIN CONDITION
- Game ends when 1 player has all chips.
- That player is declared the winner.

