# Changelog

## [Unreleased]

### Fixed
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