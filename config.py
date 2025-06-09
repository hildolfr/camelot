"""
Configuration settings for Camelot
"""

import os

# Cache settings
ENABLE_CACHE = os.getenv("CAMELOT_ENABLE_CACHE", "true").lower() == "true"
FULL_PRELOAD = os.getenv("CAMELOT_FULL_PRELOAD", "true").lower() == "true"
CACHE_DIR = os.path.expanduser(os.getenv("CAMELOT_CACHE_DIR", "~/.camelot_cache"))

# Server settings
HOST = os.getenv("CAMELOT_HOST", "0.0.0.0")
PORT = int(os.getenv("CAMELOT_PORT", "8000"))
RELOAD = os.getenv("CAMELOT_RELOAD", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("CAMELOT_LOG_LEVEL", "INFO")