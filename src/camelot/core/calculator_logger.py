"""
Calculator request logging with clean formatting and session tracking.
"""

import logging
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path


class CalculatorLogger:
    """Handles logging of poker calculator requests with session tracking."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create calculator-specific logger
        self.logger = logging.getLogger("calculator")
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Create file handler with rotation
        log_file = self.log_dir / "calculator_requests.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        
        # Create custom formatter for clean output
        formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def log_request(
        self,
        session_id: str,
        user_ip: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        execution_time_ms: float,
        cache_hit: bool,
        error: Optional[str] = None
    ):
        """Log a calculator request with clean formatting."""
        
        # Format cards for readability
        hero_hand = " ".join(request_data.get("hero_hand", []))
        board_cards = " ".join(request_data.get("board_cards", []) or []) or "None"
        
        # Build log entry
        log_parts = [
            f"SESSION: {session_id[:8]}",  # Show first 8 chars of session ID
            f"IP: {user_ip}",
            f"CARDS: {hero_hand} | Board: {board_cards}",
            f"OPPONENTS: {request_data.get('num_opponents', 0)}",
            f"MODE: {request_data.get('simulation_mode', 'default')}",
        ]
        
        # Add dynamic parameters if present
        if request_data.get("hero_position"):
            log_parts.append(f"POS: {request_data['hero_position']}")
        if request_data.get("pot_size"):
            log_parts.append(f"POT: {request_data['pot_size']}")
        if request_data.get("action_to_hero"):
            log_parts.append(f"ACTION: {request_data['action_to_hero']}")
        
        # Add result info
        if error:
            log_parts.append(f"ERROR: {error}")
        else:
            win_prob = response_data.get("win_probability", 0)
            if win_prob:
                log_parts.append(f"WIN: {win_prob:.1%}")
            vuln = response_data.get("hand_vulnerability", 0)
            if vuln:
                log_parts.append(f"VULN: {vuln:.1%}")
        
        # Add performance info
        cache_status = "CACHED" if cache_hit else "FRESH"
        log_parts.append(f"{cache_status} ({execution_time_ms:.0f}ms)")
        
        # Log the formatted entry
        self.logger.info(" | ".join(log_parts))
    
    def log_batch_request(
        self,
        session_id: str,
        user_ip: str,
        problem_count: int,
        successful_count: int,
        total_time_ms: float
    ):
        """Log a batch calculation request."""
        log_parts = [
            f"SESSION: {session_id[:8]}",
            f"IP: {user_ip}",
            "BATCH REQUEST",
            f"PROBLEMS: {problem_count}",
            f"SUCCESS: {successful_count}",
            f"TIME: {total_time_ms:.0f}ms",
            f"AVG: {total_time_ms/problem_count:.0f}ms/problem"
        ]
        
        self.logger.info(" | ".join(log_parts))
    
    def get_recent_logs(self, lines: int = 100) -> list:
        """Get recent log entries."""
        log_file = self.log_dir / "calculator_requests.log"
        if not log_file.exists():
            return []
        
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            return all_lines[-lines:] if len(all_lines) > lines else all_lines


# Create singleton instance
calculator_logger = CalculatorLogger()