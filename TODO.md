# Camelot Project TODO

## High Priority

### 1. Web UI and Base Functionalities ⏳
- [ ] Set up Flask/FastAPI web framework
- [ ] Create project directory structure
- [ ] Design base HTML/CSS templates with focus on mobile/tablet
- [ ] Implement poker calculator UI
  - [ ] Input fields for hero cards
  - [ ] Input fields for board cards
  - [ ] Opponent count selector
  - [ ] Submit button and results display
- [ ] Implement real-time calculation feedback
- [ ] Add visual card representations (Unicode suits)
- [ ] Create responsive design for mobile/tablet

### 2. REST API 📡
- [ ] Design API endpoints structure
- [ ] Implement `/api/calculate` endpoint
  - [ ] Accept hero cards, board cards, opponent count
  - [ ] Return win/tie/loss probabilities
- [ ] Add input validation
- [ ] Implement error handling
- [ ] Create API documentation
- [ ] Add CORS support for web frontend

### 3. Testing Suite 🧪
- [ ] Design test framework architecture
- [ ] Create test game generator
- [ ] Implement statistics collection
- [ ] Build web UI for test management
  - [ ] Start/stop test runs
  - [ ] Display test progress
  - [ ] Show statistical results
- [ ] Store test results in database
- [ ] Create visualization for test results

### 4. Human-Playable Poker Demo 🃏
- [ ] Design game state management
- [ ] Implement player actions (check, bet, fold, raise)
- [ ] Create AI opponents using poker_knight
- [ ] Build interactive game UI
- [ ] Add game statistics tracking
- [ ] Implement betting system
- [ ] Add hand history display

## Technical Requirements
- Python virtual environment (venv) ✅
- poker_knight module integration ✅
- Mobile/tablet optimization
- Visual appeal and user enjoyment
- Unicode card representation (♠♥♦♣)
- Texas Hold'em rules enforcement
- Support for 1v1 to 7+ player games

## Architecture Decisions
- [ ] Choose web framework (Flask vs FastAPI)
- [ ] Select frontend framework/library
- [ ] Database selection for stats storage
- [ ] WebSocket vs REST for real-time updates
- [ ] Deployment strategy

## Notes
- poker_knight module is READ ONLY - only import, never modify
- Focus on readability and information density
- All invalid poker games should error with proper logging
- Single deck enforcement (no duplicate cards)