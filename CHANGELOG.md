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

### Technical Implementation
- FastAPI application structure with modular design
- Pydantic models for request/response validation
- Core poker logic wrapper with comprehensive validation
- Mobile-optimized HTML/CSS with touch-friendly interface
- Real-time calculation feedback with loading states
- CORS support for API access

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