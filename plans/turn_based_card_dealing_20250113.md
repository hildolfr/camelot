# Turn-Based Card Dealing Architecture
Date: 2025-01-13

## Problem Statement
Currently, when players go all-in, the backend immediately:
1. Deals all remaining cards (flop, turn, river) at once
2. Determines the winner before cards are shown to players
3. Sends all this information to the frontend

This causes timing issues where players see money moving before cards are revealed, breaking the realism of the game.

## Solution Overview
Restructure the game engine to:
1. Only generate cards when explicitly requested
2. Separate card dealing from winner determination
3. Allow frontend to control the pace of card reveals

## Implementation Plan

### Phase 1: Backend Changes

#### 1.1 Modify Game State
- [ ] Add `awaiting_card_deal` flag to GameState
- [ ] Add `deal_next_phase_cards()` method separate from `_advance_phase()`
- [ ] Store pending animations separately from card dealing

#### 1.2 Refactor `_advance_phase()`
- [ ] Remove automatic card dealing from phase transitions
- [ ] Only update phase and betting state
- [ ] Return flag indicating cards need to be dealt

#### 1.3 Create New Card Dealing Endpoint
- [ ] Add `/api/game/{game_id}/deal-next-cards` endpoint
- [ ] Only deals cards for the current phase
- [ ] Returns animations for dealt cards
- [ ] Prevents dealing if cards already exist for phase

#### 1.4 Modify All-In Logic
- [ ] Remove automatic dealing of all remaining cards
- [ ] Set `awaiting_card_deal` flag when all players are all-in
- [ ] Allow frontend to control card reveal timing

### Phase 2: Frontend Changes

#### 2.1 Update Animation Queue
- [ ] Add `request_cards` animation type
- [ ] Pause animation queue when cards needed
- [ ] Request cards from backend before continuing

#### 2.2 Modify All-In Handling
- [ ] Show "All players all-in" message
- [ ] Add delay before requesting first set of cards
- [ ] Request cards phase by phase with proper delays

#### 2.3 Update Game State Management
- [ ] Track which cards have been revealed
- [ ] Prevent duplicate card requests
- [ ] Handle card dealing errors gracefully

### Phase 3: Testing & Polish

#### 3.1 Test Scenarios
- [ ] Normal betting rounds with card reveals
- [ ] All-in on pre-flop
- [ ] All-in on flop
- [ ] Multiple all-ins with side pots
- [ ] Network delays and errors

#### 3.2 Animation Timing
- [ ] Ensure smooth transitions between phases
- [ ] Add appropriate delays for drama
- [ ] Sync pot animations with card reveals

## Benefits
1. More realistic gameplay experience
2. Frontend controls pacing, not backend
3. Prevents "seeing the future" issues
4. Better separation of concerns
5. Easier to add features like:
   - Pause before revealing each card
   - Sound effects at the right time
   - Dramatic reveals for big pots

## Potential Challenges
1. State synchronization between frontend/backend
2. Handling disconnections mid-hand
3. Ensuring cards can't be dealt twice
4. Backward compatibility with existing games

## Implementation Order
1. Backend card dealing separation (1.1-1.4)
2. Frontend card request system (2.1-2.3)
3. Testing and refinement (3.1-3.2)