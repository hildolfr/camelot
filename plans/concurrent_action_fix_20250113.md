# Concurrent Action Processing Fix - Architecture Plan
Date: 2025-01-13
Status: COMPLETED - 2025-01-13

## Problem Summary
Players are losing $3 each time they fold to an all-in due to race conditions where multiple fold actions are processed simultaneously. The current `_processing_action` boolean flag is insufficient for true thread-safety.

## Root Causes
1. **Concurrent API Calls**: Multiple fold actions sent simultaneously from frontend
2. **Insufficient Locking**: Simple boolean flag doesn't prevent concurrent state modifications  
3. **No Request Deduplication**: Same action can be processed multiple times
4. **Non-Atomic State Changes**: Game state modifications aren't atomic

## Solution Architecture

### 1. Backend Thread Safety

#### A. Proper AsyncIO Locking
```python
class PokerGame:
    def __init__(self, game_config):
        # ... existing code ...
        self._action_lock = asyncio.Lock()  # Already exists but not used properly
        self._state_version = 0  # For optimistic locking
        self._request_cache = {}  # Track processed requests
        self._request_cache_ttl = 5.0  # 5 seconds TTL
```

#### B. Request ID System
- Generate unique request IDs on frontend
- Track processed requests to prevent duplicates
- Implement TTL for request cache cleanup

#### C. Atomic State Modifications
- Wrap all state changes in transactions
- Validate state before and after modifications
- Use state versioning for optimistic locking

### 2. Frontend Request Management

#### A. Request Queue System
```javascript
class ActionRequestManager {
    constructor() {
        this.pendingRequest = null;
        this.requestQueue = [];
        this.requestInFlight = false;
    }
    
    async queueAction(action, amount) {
        // Deduplicate and queue requests
        // Process one at a time
    }
}
```

#### B. Request ID Generation
- UUID v4 for each action request
- Include in API payload
- Track pending requests

#### C. UI State Management
- Disable ALL controls during request processing
- Show loading states
- Handle timeouts gracefully

### 3. State Integrity Measures

#### A. Pre/Post Validation
```python
def validate_game_state(self):
    """Comprehensive state validation"""
    # Check chip totals
    # Verify player states
    # Validate pot calculations
    # Return validation report
```

#### B. State Snapshots
- Take snapshot before action processing
- Ability to rollback on error
- Log all state transitions

#### C. Chip Tracking
```python
@dataclass
class ChipMovement:
    timestamp: float
    player_id: str
    amount: int
    reason: str
    state_before: int
    state_after: int
```

## Implementation Steps

### Phase 1: Backend Hardening (Priority: HIGH)
1. Implement proper async locking around ALL state modifications
2. Add request ID tracking and deduplication
3. Create state validation framework
4. Add comprehensive logging for all chip movements

### Phase 2: Frontend Request Management (Priority: HIGH)
1. Implement ActionRequestManager class
2. Add request ID generation
3. Update all action buttons to use queue
4. Add proper loading states and timeouts

### Phase 3: State Integrity (Priority: MEDIUM)
1. Add state versioning system
2. Implement pre/post validation
3. Create rollback mechanism
4. Add chip movement audit trail

### Phase 4: Testing & Monitoring (Priority: MEDIUM)
1. Create stress tests for concurrent actions
2. Add monitoring for duplicate requests
3. Implement alerting for chip integrity errors
4. Create debug tools for state inspection

## Code Changes Required

### 1. poker_game.py
- Wrap process_action in proper async lock
- Add request deduplication
- Implement state validation
- Add chip movement tracking

### 2. game_routes.py
- Add request ID validation
- Implement proper error responses
- Add state version checking
- Return request IDs in responses

### 3. poker_game.js
- Create ActionRequestManager
- Update all playerAction calls
- Add request ID generation
- Implement proper queue processing

### 4. models.py
- Add RequestTracking model
- Add ChipMovement model
- Add StateSnapshot model

## Success Metrics
1. Zero chip integrity errors
2. No duplicate action processing
3. Consistent state across all operations
4. Clear audit trail for all chip movements

## Rollback Plan
If issues arise:
1. Revert to synchronous action processing
2. Add global action mutex
3. Disable concurrent AI actions
4. Implement emergency state recovery

## Timeline
- Phase 1: 2-3 hours (critical fix)
- Phase 2: 1-2 hours (frontend hardening)
- Phase 3: 2-3 hours (state integrity)
- Phase 4: 1-2 hours (testing/monitoring)

Total: 6-10 hours of implementation