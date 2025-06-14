"""Logging configuration for Camelot server"""

import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Create a unique log file for this session
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
server_log_file = os.path.join(log_dir, f'server_{timestamp}.log')

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # File handler for all logs
        logging.FileHandler(server_log_file),
        # Console handler for important messages
        logging.StreamHandler()
    ]
)

# Configure specific loggers
loggers = {
    'uvicorn': logging.INFO,
    'uvicorn.error': logging.ERROR,
    'uvicorn.access': logging.INFO,
    'fastapi': logging.DEBUG,
    'src.camelot.api.game_routes': logging.DEBUG,
    'src.camelot.core.websocket_manager': logging.DEBUG,
    'websockets': logging.DEBUG,
    'asyncio': logging.WARNING,
}

for logger_name, level in loggers.items():
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

# Log startup
logging.info(f"=== Server logging initialized ===")
logging.info(f"Log file: {server_log_file}")
logging.info("="*50)