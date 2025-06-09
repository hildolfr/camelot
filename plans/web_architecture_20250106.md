# Camelot Web Architecture Plan
Date: 2025-01-06

## Framework Decision: FastAPI

### Rationale:
- Async support for real-time poker calculations
- Auto-generated API documentation (Swagger/ReDoc)
- Built-in validation with Pydantic
- WebSocket support for future real-time game features
- Excellent performance
- Modern Python with type hints

## Architecture Overview

### 1. Application Structure
```
camelot/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Project dependencies
├── src/
│   └── camelot/
│       ├── __init__.py
│       ├── api/           # REST API endpoints
│       │   ├── __init__.py
│       │   ├── calculator.py
│       │   └── models.py  # Pydantic models
│       ├── web/           # Web UI routes
│       │   ├── __init__.py
│       │   └── routes.py
│       ├── core/          # Business logic
│       │   ├── __init__.py
│       │   └── poker_logic.py
│       └── utils/         # Utilities
│           ├── __init__.py
│           └── validators.py
├── static/                # Static files
│   ├── css/
│   ├── js/
│   └── images/
├── templates/             # Jinja2 templates
│   └── index.html
└── poker_knight/          # READ ONLY module

```

### 2. Core Components

#### A. FastAPI Application (main.py)
- [ ] Initialize FastAPI app
- [ ] Configure CORS for API access
- [ ] Mount static files
- [ ] Include API and web routers
- [ ] Add exception handlers

#### B. API Module (src/camelot/api/)
- [ ] Calculator endpoint: POST /api/calculate
- [ ] Input validation with Pydantic models
- [ ] Response models for consistent API output
- [ ] Error handling middleware

#### C. Web Module (src/camelot/web/)
- [ ] Main page route: GET /
- [ ] Calculator page with form
- [ ] Results display
- [ ] Mobile-responsive design

#### D. Core Logic (src/camelot/core/)
- [ ] Wrapper around poker_knight module
- [ ] Input sanitization
- [ ] Result formatting
- [ ] Game validation

### 3. Frontend Design

#### Mobile-First Approach
- Responsive grid system
- Touch-friendly card selection
- Visual card representations
- Loading states for calculations
- Clear result display

#### UI Components
1. Card Selector
   - Visual grid of cards
   - Unicode suit display (♠♥♦♣)
   - Selected state indication

2. Board Input
   - Progressive reveal (flop, turn, river)
   - Validation for duplicate cards

3. Opponent Selector
   - Slider or buttons (1-7 opponents)
   - Visual representation

4. Results Display
   - Win/Tie/Loss percentages
   - Confidence intervals
   - Hand strength indicators

### 4. Implementation Steps

1. **Phase 1: Basic Setup** ✓
   - Create requirements.txt
   - Set up FastAPI application
   - Basic routing structure

2. **Phase 2: Poker Calculator**
   - Integrate poker_knight
   - Create API endpoint
   - Build basic UI

3. **Phase 3: Enhanced UI**
   - Mobile optimization
   - Visual improvements
   - Real-time feedback

4. **Phase 4: Testing & Polish**
   - Unit tests
   - Integration tests
   - Performance optimization

### 5. Dependencies

Core:
- fastapi
- uvicorn (ASGI server)
- jinja2 (templating)
- python-multipart (form data)

Development:
- pytest
- httpx (testing)
- black (formatting)
- flake8 (linting)

### 6. Success Criteria

- [ ] Calculator returns results in <100ms
- [ ] Mobile-friendly UI (tested on various devices)
- [ ] Clean, intuitive interface
- [ ] Proper error handling
- [ ] API documentation auto-generated
- [ ] All poker rules enforced

## Next Steps

1. Create requirements.txt with all dependencies
2. Implement basic FastAPI structure
3. Create poker calculator endpoint
4. Design mobile-first HTML template
5. Add interactive JavaScript for card selection