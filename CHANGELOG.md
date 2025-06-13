# Changelog

## [Unreleased]

### Added
- Hand history tracking for poker game
  - Records all completed hands with board cards, winners, and pot amounts
  - Accessible via 📜 Hand History button during gameplay
  - Shows most recent hands first with winner information
  - API endpoint `/api/game/{game_id}/hand-history`

### Fixed
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