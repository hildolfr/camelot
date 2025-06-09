#!/bin/bash
# Camelot startup script

echo "🏰 Starting Camelot Poker Calculator..."

# Activate virtual environment
source venv/bin/activate

# Add poker_knight to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/poker_knight"

# Run the FastAPI application
echo "📡 Starting server on http://localhost:8000"
echo "📚 API docs available at http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop the server"

# For production, use uvicorn directly with reload disabled
# uvicorn main:app --host 0.0.0.0 --port 8000

# For development with auto-reload
python main.py