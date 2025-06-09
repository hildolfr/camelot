# ⚔️ Camelot - Poker Calculator Web Interface

Camelot is a web interface and REST API for Texas Hold'em poker calculations, powered by the Poker Knight module.

## Features

- 🃏 **Visual Card Selection**: Interactive, mobile-friendly card selector
- 📊 **Real-time Calculations**: Fast poker odds calculation with confidence intervals
- 🌐 **REST API**: Full-featured API for programmatic access
- 📱 **Mobile Optimized**: Responsive design for phones and tablets
- 🎨 **Beautiful UI**: Visually appealing interface with smooth animations

## Quick Start

1. **Activate the virtual environment** (if not already activated):
   ```bash
   source venv/bin/activate
   ```

2. **Run the application**:
   ```bash
   ./run.sh
   ```
   Or directly:
   ```bash
   python main.py
   ```

3. **Open your browser** and navigate to:
   - Web UI: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs

## Usage

### Web Interface

1. **Select Your Cards**: Click on two cards to select your hole cards
2. **Add Board Cards** (Optional): Select 3-5 community cards for flop/turn/river
3. **Choose Opponents**: Select the number of opponents (1-6)
4. **Calculate**: Click "Calculate Odds" to get your probabilities

### REST API

Calculate poker odds via the API:

```bash
curl -X POST "http://localhost:8000/api/calculate" \
  -H "Content-Type: application/json" \
  -d '{
    "hero_hand": ["A♠", "K♠"],
    "num_opponents": 2,
    "board_cards": ["Q♠", "J♦", "10♥"],
    "simulation_mode": "default"
  }'
```

Response:
```json
{
  "success": true,
  "win_probability": 0.823,
  "tie_probability": 0.012,
  "loss_probability": 0.165,
  "simulations_run": 100000,
  "execution_time_ms": 125.4,
  "confidence_interval": [0.820, 0.826],
  "hand_categories": {...}
}
```

## Project Structure

```
camelot/
├── main.py              # FastAPI application entry point
├── src/camelot/
│   ├── api/            # REST API endpoints
│   ├── core/           # Business logic
│   └── web/            # Web UI routes
├── static/             # CSS, JavaScript, images
├── templates/          # HTML templates
└── poker_knight/       # Poker calculation engine (READ ONLY)
```

## Development

### Running Tests
```bash
python test_basic.py
```

### API Endpoints

- `GET /` - Main web interface
- `GET /api/health` - Health check endpoint
- `POST /api/calculate` - Calculate poker odds
- `GET /api/docs` - Interactive API documentation

### Card Format

Cards use Unicode suits:
- ♠ (spades)
- ♥ (hearts)
- ♦ (diamonds)
- ♣ (clubs)

Example: `A♠`, `K♥`, `10♦`, `2♣`

## Future Features

- 🧪 Testing suite with statistics collection
- 🎮 Human-playable poker demo game
- 💾 Database integration for game history
- 🔌 WebSocket support for real-time games

## License

This project is created by github user hildolfr.