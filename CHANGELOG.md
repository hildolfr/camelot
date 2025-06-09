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