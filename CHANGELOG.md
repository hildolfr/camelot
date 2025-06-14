# Changelog

## [Unreleased]

### Added
- Real-time WebSocket support for game updates
  - WebSocket connection manager for game rooms
  - Bidirectional communication for instant updates
  - Automatic reconnection with exponential backoff
  - Connection status indicator in UI
  - Broadcast updates to all connected players/spectators
  - HTTP fallback for compatibility
  - Ping/pong keepalive mechanism
  - Support for concurrent connections to same game

### Added
- Comprehensive concurrent action handling system
  - Added AsyncIO locking to prevent race conditions in action processing
  - Implemented request ID tracking and deduplication to prevent duplicate actions
  - Added ActionRequestManager class in frontend to queue and throttle requests
  - Added chip movement audit trail for debugging chip integrity issues
  - Enhanced state validation framework with comprehensive checks
  - Created test suite for concurrent action scenarios
  - Implemented state snapshot and rollback mechanism for error recovery
  - Added game monitoring system with metrics and alerting
  - Created debug tools for live state inspection and troubleshooting
  - Added formal Pydantic models for request tracking and state management

### Added
- Hand history tracking for poker game
  - Records all completed hands with board cards, winners, and pot amounts
  - Accessible via 📜 Hand History button during gameplay
  - Shows most recent hands first with winner information
  - API endpoint `/api/game/{game_id}/hand-history`
- Turn-based card dealing system for more realistic gameplay
  - Cards are now only generated when explicitly requested by frontend
  - New API endpoints: `/api/game/{game_id}/deal-next-cards` and `/api/game/{game_id}/advance-all-in-phase`
  - Frontend controls the pace of card reveals, preventing "seeing the future" issues
  - All-in situations now show cards phase by phase with proper delays

### Changed
- Removed redundant "Victory is yours" modal before game over screen
  - Players already see elimination messages, making this redundant
  - Reduces UI clutter and speeds up game flow

### Fixed
- Fixed game over screen blocking bug report button
  - Removed overlay completely, now shows only centered modal
  - Bug report button remains fully accessible during game over
- Fixed broken "Play Again" button link
  - Added /poker route that shows lobby on home page
  - Now correctly redirects to poker lobby section
- Fixed bug report modal being obscured by game over screen
  - Moved bug report modal to bottom center of screen
  - Reduced game over modal z-index to stay below bug report
- Implemented visual pot representation with chip animations
  - Chips now animate from players to central pot when betting
  - Pot chips visually accumulate in center of table
  - Winner receives chips from pot with smooth animation
  - Fixes timing issue where AI appeared to take money before winning
- Fixed critical double-payment bug when players fold to all-in
  - Winner was receiving uncalled bet refund AND winning a pot with their full bet
  - Now clears all player bets after handling uncalled returns to prevent double-counting
  - Addresses user report: "why did I just win double?" with $402 extra chips
- Fixed visual bug where winner's stack updated before pot animation
  - Now sends pre-win stack value with award_pot animation
  - Stack shows correct amount until pot animation completes
  - Addresses user report: "ai got my money before I even lost!"
- Fixed critical chip creation bug in pot calculation when players fold to all-in
  - Bug was double-counting winner's contribution when returning uncalled bets
  - Now correctly calculates pot from folded players only plus winner's matched amount
  - Added chip integrity validation at start of each hand to catch issues early
  - Addresses user report: "weird money stuff happening again" with $393 extra chips
- Fixed celebration animation (confetti) playing when AI wins instead of only when hero wins
  - Bug was in animateCelebration function which created confetti for any winner
  - Now checks if winner_id === 'hero' before creating confetti effects
- Reverted visual bug fix that was causing incorrect stack displays
  - The fix was subtracting pot amount from winner's stack, causing negative values
- Changed misleading error log "No active players found to act!" to info level
  - This is normal behavior when all players are all-in
- Fixed TypeScript warnings for unused variables in poker_game.js
- Fixed critical pot calculation bug that was creating extra chips by accumulating pots across betting rounds
  - Changed pot calculation to only run once at showdown instead of after each betting round
  - Renamed `total_bet_this_round` to `total_bet_this_hand` for clarity
  - Added validation to ensure pot totals never exceed total chips in play
  - Bug was discovered through user bug report system showing pots totaling more than starting chips
- Fixed game over screen overlay blocking bug report button
  - Reduced game over overlay z-index from 9998 to 9000
  - Boosted bug report button z-index to ensure it stays accessible
  - Bug report button now remains clickable even when game over screen is displayed

### Added
- Hand strength indicator showing win probability and current hand
- Pot odds calculator for better decision making
- Enhanced animations and visual feedback
- Calculator logging system for debugging
- Comprehensive bug fixes for all-in showdown visibility
- Z-index fix for bug report button visibility

### Changed
- Improved AI decision making with hand evaluation
- Enhanced UI responsiveness and performance
- Better error handling and logging throughout

## Previous Updates
- Added bug reporting system with dedicated logging
- Implemented poker game engine with Texas Hold'em rules
- Added navigation bar and lobby interface
- Integrated poker_knightng GPU-accelerated solver