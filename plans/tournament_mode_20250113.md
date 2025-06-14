# Tournament Mode Implementation Plan
Date: 2025-01-13
Status: PROPOSED

## Overview
Implement tournament poker functionality starting with Sit & Go tournaments, then expanding to multi-table tournaments (MTTs).

## Why Tournaments?
1. **Massive Replay Value** - Players love the competitive format
2. **Natural Progression** - Players can improve and climb leaderboards
3. **Monetization Ready** - Tournament buy-ins are a proven model
4. **Social Features** - Tournaments create communities
5. **Showcases AI** - ICM-aware AI decisions are impressive

## Phase 1: Sit & Go Tournaments

### Core Features
1. **Tournament Lobby**
   - List of available tournaments
   - Buy-in amounts and prize structures
   - Player count (6-max, 9-max)
   - Registration status
   - Quick-join buttons

2. **Blind Structure**
   ```python
   blind_levels = [
       {"level": 1, "small": 10, "big": 20, "ante": 0, "duration": 600},
       {"level": 2, "small": 15, "big": 30, "ante": 0, "duration": 600},
       {"level": 3, "small": 20, "big": 40, "ante": 5, "duration": 600},
       {"level": 4, "small": 30, "big": 60, "ante": 10, "duration": 600},
       # ... continues
   ]
   ```

3. **Tournament State Management**
   ```python
   class TournamentState:
       tournament_id: str
       type: str  # "sit_n_go", "mtt"
       buy_in: int
       starting_stack: int
       blind_levels: List[BlindLevel]
       current_level: int
       level_start_time: float
       players: List[TournamentPlayer]
       prize_pool: int
       payouts: List[int]  # [50%, 30%, 20%] for top 3
       status: str  # "registering", "running", "finished"
   ```

4. **ICM Integration**
   - Real-time ICM calculations for AI decisions
   - Bubble factor adjustments
   - Risk-averse play near money positions
   - Tournament equity display

5. **Prize Distribution**
   - Automatic payout calculation
   - In-the-money (ITM) notifications
   - Final table celebrations
   - Tournament history tracking

### Backend Changes

#### 1. Tournament Manager
```python
class TournamentManager:
    def __init__(self):
        self.tournaments: Dict[str, Tournament] = {}
        self.player_tournaments: Dict[str, List[str]] = {}
    
    async def create_tournament(self, config: TournamentConfig) -> Tournament:
        # Create new tournament
        # Set up blind structure
        # Initialize prize pool
    
    async def register_player(self, tournament_id: str, player_id: str):
        # Add player to tournament
        # Check if tournament should start
        # Handle late registration
    
    async def advance_blinds(self, tournament_id: str):
        # Move to next blind level
        # Broadcast blind change
        # Update all tables
```

#### 2. Modified Game Engine
- Add tournament context to game state
- Implement blind progression
- Add ante support
- Calculate ICM pressure for AI

#### 3. WebSocket Events
- `tournament_registered` - Player joins
- `tournament_started` - Tournament begins
- `blinds_increased` - Level change
- `player_eliminated` - Bust out
- `tournament_finished` - Winners determined

### Frontend Changes

#### 1. Tournament Lobby Page
```html
<div class="tournament-lobby">
    <h2>Sit & Go Tournaments</h2>
    <div class="tournament-filters">
        <button>All</button>
        <button>Low Stakes</button>
        <button>High Stakes</button>
    </div>
    <div class="tournament-list">
        <!-- Tournament cards -->
    </div>
</div>
```

#### 2. Tournament HUD
- Blind level timer
- Average stack display
- Position / total players
- Payout positions
- ICM equity (optional)

#### 3. Elimination Animations
- Bust-out animation
- "Finished in Xth place" message
- Payout notification if ITM
- Spectator mode after elimination

## Phase 2: Multi-Table Tournaments

### Additional Features
1. **Table Balancing**
   - Automatic reseating
   - Table breaking algorithm
   - Maintain position fairness

2. **Late Registration**
   - Allow joining for X blind levels
   - Adjust starting stack
   - Update prize pool dynamically

3. **Tournament Types**
   - Turbo (fast blinds)
   - Deep stack
   - Knockout bounties
   - Rebuy tournaments

4. **Advanced Features**
   - Hand-for-hand on bubble
   - Final table streaming
   - Spectator chat
   - Tournament statistics

## Phase 3: Tournament Series

### Features
1. **Leaderboards**
   - Points system
   - Season rankings
   - Achievements

2. **Special Events**
   - Weekly tournaments
   - Championship events
   - Freerolls

3. **Social Features**
   - Tournament chat
   - Friend invites
   - Private tournaments

## Technical Considerations

### Performance
- Efficient table balancing algorithms
- Optimized ICM calculations
- Caching tournament states
- WebSocket room per tournament

### Scalability
- Redis for tournament state
- Horizontal scaling for multiple tournaments
- Load balancing across servers

### Data Storage
```sql
CREATE TABLE tournaments (
    id UUID PRIMARY KEY,
    type VARCHAR(20),
    buy_in INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

CREATE TABLE tournament_players (
    tournament_id UUID,
    player_id VARCHAR(50),
    position INTEGER,
    payout INTEGER,
    hands_played INTEGER
);
```

## Success Metrics
1. **Engagement**
   - Tournaments started per day
   - Average tournament duration
   - Re-registration rate

2. **Competitive Health**
   - Skill distribution
   - ROI variance
   - Time to ITM

3. **Technical**
   - Tournament completion rate
   - Average latency
   - Concurrent tournament capacity

## Implementation Timeline
- Phase 1 (Sit & Go): 2-3 days
- Phase 2 (MTT): 3-4 days
- Phase 3 (Series): 2-3 days

Total: 7-10 days for full tournament system

## Why This Is The Best Next Feature

1. **User Retention** - Tournaments create long-term goals
2. **Natural Monetization** - Buy-ins are expected
3. **Social Proof** - Visible player counts
4. **Skill Progression** - Clear improvement path
5. **Content Creation** - Streamable final tables
6. **AI Showcase** - ICM decisions are fascinating
7. **Marketing Hook** - "Daily $10K Guaranteed"

The tournament system would transform Camelot from a casual poker game into a competitive platform that players return to daily.