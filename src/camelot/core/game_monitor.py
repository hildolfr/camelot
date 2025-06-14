"""Game monitoring and alerting system"""

import logging
import time
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class GameMonitor:
    """Monitor game health and track metrics"""
    
    def __init__(self):
        # Metrics storage
        self.duplicate_requests = defaultdict(list)  # game_id -> list of duplicate events
        self.chip_integrity_errors = defaultdict(list)  # game_id -> list of errors
        self.action_metrics = defaultdict(lambda: {
            "total": 0,
            "duplicates": 0,
            "errors": 0,
            "by_type": defaultdict(int)
        })
        
        # Sliding window for rate tracking (last 5 minutes)
        self.request_window = deque(maxlen=300)  # 5 min at 1 sec resolution
        self.error_window = deque(maxlen=300)
        
        # Alert thresholds
        self.alert_thresholds = {
            "duplicate_rate": 0.1,  # Alert if >10% of requests are duplicates
            "error_rate": 0.05,  # Alert if >5% of requests error
            "chip_integrity_errors_per_hour": 1,  # Alert if any chip errors
            "requests_per_second": 10  # Alert if >10 requests/sec sustained
        }
        
        # Alert callbacks
        self.alert_callbacks = []
        
    def record_request(self, game_id: str, player_id: str, action: str, 
                      request_id: Optional[str], is_duplicate: bool = False):
        """Record an action request"""
        timestamp = time.time()
        
        # Update metrics
        self.action_metrics[game_id]["total"] += 1
        self.action_metrics[game_id]["by_type"][action] += 1
        
        if is_duplicate:
            self.action_metrics[game_id]["duplicates"] += 1
            self.duplicate_requests[game_id].append({
                "timestamp": timestamp,
                "player_id": player_id,
                "action": action,
                "request_id": request_id
            })
            
            # Check duplicate rate
            total = self.action_metrics[game_id]["total"]
            duplicates = self.action_metrics[game_id]["duplicates"]
            if total > 10 and duplicates / total > self.alert_thresholds["duplicate_rate"]:
                self._trigger_alert("high_duplicate_rate", {
                    "game_id": game_id,
                    "rate": duplicates / total,
                    "total_requests": total,
                    "duplicates": duplicates
                })
        
        # Track request rate
        current_second = int(timestamp)
        self.request_window.append(current_second)
        
    def record_error(self, game_id: str, error_type: str, details: Dict[str, Any]):
        """Record an error event"""
        timestamp = time.time()
        
        self.action_metrics[game_id]["errors"] += 1
        
        if error_type == "chip_integrity":
            self.chip_integrity_errors[game_id].append({
                "timestamp": timestamp,
                "details": details
            })
            
            # Check chip integrity error rate
            recent_errors = [e for e in self.chip_integrity_errors[game_id] 
                           if timestamp - e["timestamp"] < 3600]  # Last hour
            
            if len(recent_errors) >= self.alert_thresholds["chip_integrity_errors_per_hour"]:
                self._trigger_alert("chip_integrity_violation", {
                    "game_id": game_id,
                    "errors_in_hour": len(recent_errors),
                    "latest_error": details
                })
        
        # Track error rate
        current_second = int(timestamp)
        self.error_window.append(current_second)
        
        # Check overall error rate
        total = self.action_metrics[game_id]["total"]
        errors = self.action_metrics[game_id]["errors"]
        if total > 20 and errors / total > self.alert_thresholds["error_rate"]:
            self._trigger_alert("high_error_rate", {
                "game_id": game_id,
                "rate": errors / total,
                "total_requests": total,
                "errors": errors
            })
    
    def get_metrics(self, game_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current metrics"""
        if game_id:
            return {
                "game_id": game_id,
                "metrics": self.action_metrics.get(game_id, {}),
                "duplicate_requests": len(self.duplicate_requests.get(game_id, [])),
                "chip_errors": len(self.chip_integrity_errors.get(game_id, [])),
                "timestamp": datetime.now().isoformat()
            }
        
        # Global metrics
        total_games = len(self.action_metrics)
        total_requests = sum(m["total"] for m in self.action_metrics.values())
        total_duplicates = sum(m["duplicates"] for m in self.action_metrics.values())
        total_errors = sum(m["errors"] for m in self.action_metrics.values())
        
        # Calculate rates
        current_time = int(time.time())
        recent_requests = sum(1 for t in self.request_window if current_time - t < 60)
        recent_errors = sum(1 for t in self.error_window if current_time - t < 60)
        
        return {
            "summary": {
                "active_games": total_games,
                "total_requests": total_requests,
                "total_duplicates": total_duplicates,
                "total_errors": total_errors,
                "duplicate_rate": total_duplicates / total_requests if total_requests > 0 else 0,
                "error_rate": total_errors / total_requests if total_requests > 0 else 0,
                "requests_per_minute": recent_requests,
                "errors_per_minute": recent_errors
            },
            "by_game": {
                game_id: self.get_metrics(game_id)
                for game_id in self.action_metrics.keys()
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def add_alert_callback(self, callback):
        """Add a callback for alerts"""
        self.alert_callbacks.append(callback)
    
    def _trigger_alert(self, alert_type: str, data: Dict[str, Any]):
        """Trigger an alert"""
        alert = {
            "type": alert_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        logger.error(f"ALERT: {alert_type} - {json.dumps(data, indent=2)}")
        
        # Call all registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
    
    def get_game_health(self, game_id: str) -> Dict[str, Any]:
        """Get health status for a specific game"""
        metrics = self.action_metrics.get(game_id, {})
        
        if not metrics or metrics["total"] == 0:
            return {
                "game_id": game_id,
                "status": "unknown",
                "message": "No data available"
            }
        
        # Calculate rates
        duplicate_rate = metrics["duplicates"] / metrics["total"]
        error_rate = metrics["errors"] / metrics["total"]
        
        # Determine health status
        if error_rate > self.alert_thresholds["error_rate"]:
            status = "critical"
            message = f"High error rate: {error_rate:.2%}"
        elif duplicate_rate > self.alert_thresholds["duplicate_rate"]:
            status = "warning"
            message = f"High duplicate rate: {duplicate_rate:.2%}"
        elif game_id in self.chip_integrity_errors:
            status = "warning"
            message = f"Chip integrity errors detected: {len(self.chip_integrity_errors[game_id])}"
        else:
            status = "healthy"
            message = "Game running normally"
        
        return {
            "game_id": game_id,
            "status": status,
            "message": message,
            "metrics": {
                "total_actions": metrics["total"],
                "duplicate_rate": duplicate_rate,
                "error_rate": error_rate,
                "action_breakdown": dict(metrics["by_type"])
            },
            "timestamp": datetime.now().isoformat()
        }


# Global monitor instance
game_monitor = GameMonitor()