# Camelot Changelog

All notable changes to the Camelot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup with Python virtual environment
- Cloned poker_knight module from github.com/hildolfr/poker_knight
- Created project structure with TODO.md and CHANGELOG.md
- Established project goals and development roadmap
- Implemented FastAPI web framework with async support
- Created poker calculator backend wrapper around poker_knight
- Built REST API with `/api/calculate` endpoint for poker odds calculation
- Designed mobile-first responsive web UI with visual card selection
- Added interactive JavaScript for real-time card selection and results display
- Implemented input validation for cards and game rules
- Created visually appealing UI with animations and gradient backgrounds
- Git repository initialization with proper commit structure
- Fixed calculate button responsiveness and z-index issues
- Fixed particle effects spawning at top of page
- Added card sorting by suit for easier selection
- Implemented side panel for desktop results display
- Fixed HTTP 422 validation errors with proper board card rules
- Created ResultAdapter to handle poker_knight type inconsistencies
- Doubled particle density for enhanced visual effects
- Added history ticker with past calculations
- Implemented full history modal with detailed calculation records
- Removed ticker based on user feedback (visually distracting)
- Enhanced history UI with:
  - Game phase filters (All, Pre-flop, Flop, Turn, River)
  - Statistics dashboard showing aggregate data
  - Clear history functionality with confirmation dialog
  - Smooth animations and hover effects
  - Color-coded result indicators
  - Shimmer effects on statistics panel
  - Imploding animation when clearing history (staggered effect)
  - Visual poker table representation for selected history items
  - Interactive history items that show game visualization
  - Realistic poker table with cards displayed as on a real table
  - Game details panel with win rate, opponents, stage, and time
  - Fixed pre-flop visualization to show empty table (no blank cards)
- Added progressive statistics dropdown to results panel:
  - Basic: Just win rate and hand strength meter
  - Standard: Common metrics (win rate, speed, simulations) - default
  - Advanced: Detailed breakdown with confidence intervals and hand categories
  - Mathematician: Complete analysis with equity, pot odds, EV, and distribution data
  - Replaced tabs with cleaner dropdown menu to prevent overflow
  - User's detail level preference is saved and restored between sessions
  - Modified Standard view: removed simulation count/speed, added likely hand outcomes
  - Added Expert view with advanced poker metrics:
    - Core metrics: win rate, total equity, pot odds needed
    - Strategic insights: hand classification, recommended actions, bluff frequencies
    - Placeholder for advanced features (ICM, position, multi-way stats)
    - Note about additional parameters needed for tournament features
- Redesigned loading indicator:
  - Moved to inline position next to opponent selector (no overlay)
  - Smaller animated shuffling cards that don't disrupt layout
  - "Calculating..." text only
  - Uses available space efficiently
- Moved win/loss/tie percentages below the colored bar for better readability
- Updated Math Mode to show ALL available statistics with maximum precision
- Added Tournament Mode with advanced features:
  - Toggle switch to enable tournament-specific options
  - Position selector (Button, SB, BB, UTG, MP, CO, etc.)
  - Dynamic stack size inputs for hero and each opponent
  - Stack sizes in big blinds for ICM calculations
  - Automatically adjusts inputs based on number of opponents
  - API support for position-aware equity and ICM calculations
- Added position help modal explaining all table positions
- Enhanced Expert view with actionable strategy recommendations
- Modified card display to show rank and suit in both corners (top-left and bottom-right)
- Fixed card display bug showing multiple suits by:
  - Removing redundant center element
  - Restructuring card corners with proper div containers
  - Correcting rotation (only bottom-right corner should rotate)
  - Simplifying CSS for card corner elements
- Reorganized card selection interface:
  - Cards now displayed in separate rows by suit
  - Added suit symbols as row labels
  - Improved card accessibility and findability
  - Fixed card sizing for better row layout
  - Added mobile-responsive adjustments for row view
  - Implemented smart card scaling to keep all suits on one row when possible
  - Cards dynamically resize between 40px-70px width to fit available space
  - Only splits to 2 rows per suit on very small screens (<500px) as last resort
  - Card corner text scales proportionally with card size
  - Improved text readability on scaled cards:
    - Fixed font sizes for card corners (0.75rem default, 0.7rem on small screens)
    - Reduced card border thickness to maximize content space
    - Adjusted selection badge size to not overwhelm small cards
    - Text remains readable even at minimum card size (35px)
- Added help icons to Expert view explaining poker terminology:
  - Core Metrics: Total Equity, Pot Odds Needed
  - Strategic Insights: Hand Class, Recommended Action, Bluff Frequency
  - Advanced Features: ICM, Position, Defense, SPR explanations
  - Mobile-friendly tooltips with tap support
- Fixed Expert view tournament note to only show when pot size is 0
- Improved tooltip z-index and positioning to prevent overlap issues
- Fixed tournament mode persistence issues:
  - Tournament mode state now saved to localStorage
  - Position, stack sizes, and pot size are preserved between sessions
  - Tournament options panel correctly shows on page load when mode is enabled
  - All tournament inputs restore their values from previous session
- Fixed tournament features integration with poker_knight:
  - poker_knight v1.5.0 DOES support ICM equity, position-aware equity, and SPR calculations
  - Issue was missing fields in ResultAdapter and API models
  - Added support for: tournament_pressure, fold_equity_estimates, bubble_factor, bluff_catching_frequency
  - Some features (defense_frequencies, multi_way_statistics) return None in certain scenarios
  - Tournament features now properly display when pot size > 0 and tournament mode is enabled
- Added help icons to Expert statistics view:
  - Inline question mark icons next to complex poker terms
  - Hover tooltips explaining technical terminology
  - Mobile-friendly tap interactions for tooltips
- Fixed tooltip positioning issues in Expert view:
  - Changed from nested tooltips to dynamic positioning system
  - Tooltips now use fixed positioning to avoid being cut off by containers
  - Smart positioning that keeps tooltips on screen (above/below as needed)
  - Single tooltip element reused for all help icons for better performance
  - Increased z-index to 10000 to ensure tooltips appear above all other elements
- Enhanced Expert and Math tabs with new tournament statistics:
  - Expert tab now includes strategic interpretations for:
    - Stack Dynamics (big/average/short stack strategies)
    - Fold Equity (position-based betting adjustments)
    - Bluff Catching Frequency (when to call vs fold)
  - Math tab shows raw values for all tournament features:
    - tournament_pressure object with stack percentages
    - fold_equity_estimates with position modifiers
    - bubble_factor and bluff_catching_frequency values
    - Pretty-printed JSON for complex objects
  - All new stats have help tooltips explaining their meaning
  - Added Multi-way Dynamics interpretation for games with 3+ opponents
- Fixed visual issues:
  - Removed scrollbar from results panel (hidden but still scrollable)
  - Fixed Core Metrics tooltips being obscured by using horizontal positioning
  - Tooltips for Total Equity and Pot Odds now appear to the left/right instead of above
  - Removed tooltip arrow for cleaner appearance with dynamic positioning
  - Explanations for: Total Equity, Pot Odds, ICM, SPR, Bluff Frequency, etc.
  - CSS styling for help icons with smooth animations
  - Event delegation for dynamically created help elements
  - Reorganized Advanced Strategic Adjustments with grid layout:
    - Better visual separation between metrics and advice
    - Each item in its own container with subtle background
    - Consistent column widths for improved readability
- Added interactive charts using Chart.js:
  - Win/Tie/Loss Donut Chart replacing horizontal bars
    - Animated donut chart with percentages
    - Total equity displayed in center
    - Color-coded segments (green/yellow/red)
    - Responsive and mobile-friendly
  - Hand Categories Horizontal Bar Chart
    - Visual representation of likely hand outcomes
    - Color-coded bars from strongest to weakest
    - Animated entry with staggered delays
    - Replaces text list in Standard/Advanced views
    - Values displayed directly on bars
- Implemented extensive caching system:
  - Leverages poker_knight's built-in unified cache with SQLite persistence
  - Cache stored in `~/.camelot_cache/` to avoid file watcher issues
  - Priority hands cached immediately at startup (~25 hands, <5 seconds)
  - Full preflop cache warming in background (1,326 hands × 6 opponents = 7,956 scenarios)
  - Common board patterns cached for frequent flop textures
  - Cache persists between daemon restarts
  - API endpoint `/api/cache-status` to monitor cache progress
  - Expected performance: 2000x speedup for cached queries (<1ms vs 100-2000ms)
  - Watchfiles configured to exclude cache files from reload triggers

### Technical Implementation
- FastAPI application structure with modular design
- Pydantic models for request/response validation
- Core poker logic wrapper with comprehensive validation
- Mobile-optimized HTML/CSS with touch-friendly interface
- Real-time calculation feedback with loading states
- CORS support for API access
- LocalStorage for history persistence
- Responsive filter system for history browsing

### Fixed
- Calculate button z-index and responsiveness issues
- Particle spawning location (now bottom/middle only)
- HTTP 422 errors with invalid board card configurations
- Type mismatch errors from poker_knight confidence_interval
- Timer display showing "NaNd ago" in history
- Visual clutter from ticker implementation

### Planning
- Testing suite with statistics collection
- Human-playable poker demo game
- Database integration for stats storage
- WebSocket support for real-time games

## [0.1.0] - 2025-01-06

### Added
- Complete web UI and REST API implementation
- Poker calculator with visual card selection
- Mobile-responsive design
- Real-time calculation feedback
- API documentation with Swagger UI
- Basic test suite
- README documentation
- Startup script for easy deployment

### MVP Complete
- Web UI with poker calculator ✅
- REST API for external integration ✅
- Mobile/tablet optimization ✅
- Visual card interface ✅
- Input validation and error handling ✅

## [0.0.1] - 2025-01-06

### Added
- Project initialization
- CLAUDE.md with project specifications
- Basic directory structure