#!/bin/bash

# Activate virtual environment
source venv/bin/activate

# Get timestamp for log file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/server_${TIMESTAMP}.log"

echo "Starting Camelot server..."
echo "Log file: $LOG_FILE"
echo "Server will be available at http://localhost:8000"
echo ""
echo "Latest log file will always be available at: logs/server_latest.log"

# Create symlink to latest log
ln -sf "server_${TIMESTAMP}.log" logs/server_latest.log

# Start server without hot reload to avoid file watching issues
CAMELOT_RELOAD=false python main.py 2>&1 | tee $LOG_FILE