"""
Adapter to handle various return formats from poker_knight module.
This ensures consistent API responses regardless of poker_knight version changes.
"""

from typing import Dict, Any, Tuple, Optional, Union


class ResultAdapter:
    """Adapts poker_knight results to consistent API format."""
    
    @staticmethod
    def normalize_confidence_interval(value: Any) -> Tuple[float, float]:
        """Convert confidence interval to tuple format."""
        if isinstance(value, tuple) and len(value) == 2:
            return value
        elif isinstance(value, list) and len(value) == 2:
            return tuple(value)
        elif isinstance(value, dict):
            # Handle dict format with 'low'/'high' or 'lower'/'upper' keys
            if 'low' in value and 'high' in value:
                return (float(value['low']), float(value['high']))
            elif 'lower' in value and 'upper' in value:
                return (float(value['lower']), float(value['upper']))
        
        # Default fallback
        return (0.0, 1.0)
    
    @staticmethod
    def adapt_simulation_result(result: Any) -> Dict[str, Any]:
        """
        Adapt a SimulationResult object to a consistent dictionary format.
        Handles various return formats and missing fields gracefully.
        """
        # Start with required fields, using safe attribute access
        adapted = {
            "win_probability": getattr(result, 'win_probability', 0.0),
            "tie_probability": getattr(result, 'tie_probability', 0.0),
            "loss_probability": getattr(result, 'loss_probability', 0.0),
            "simulations_run": getattr(result, 'simulations_run', 0),
            "execution_time_ms": getattr(result, 'execution_time_ms', 0.0),
        }
        
        # Handle confidence interval
        confidence_interval = getattr(result, 'confidence_interval', None)
        adapted["confidence_interval"] = ResultAdapter.normalize_confidence_interval(confidence_interval)
        
        # Handle hand categories (might be dict or missing)
        hand_categories = getattr(result, 'hand_category_frequencies', {})
        if hand_categories is None:
            hand_categories = {}
        adapted["hand_categories"] = dict(hand_categories)  # Ensure it's a dict
        
        # Advanced features (optional, may not exist)
        # Position aware equity
        if hasattr(result, 'position_aware_equity'):
            pae = getattr(result, 'position_aware_equity')
            if isinstance(pae, dict):
                adapted["position_aware_equity"] = pae
        
        # ICM equity
        if hasattr(result, 'icm_equity'):
            adapted["icm_equity"] = getattr(result, 'icm_equity')
        
        # Multi-way statistics
        if hasattr(result, 'multi_way_statistics'):
            mws = getattr(result, 'multi_way_statistics')
            if isinstance(mws, dict):
                # Ensure all nested values are JSON serializable
                adapted["multi_way_statistics"] = ResultAdapter._sanitize_dict(mws)
        
        # Defense frequencies
        if hasattr(result, 'defense_frequencies'):
            df = getattr(result, 'defense_frequencies')
            if isinstance(df, dict):
                adapted["defense_frequencies"] = df
        
        # Coordination effects
        if hasattr(result, 'coordination_effects'):
            ce = getattr(result, 'coordination_effects')
            if isinstance(ce, dict):
                adapted["coordination_effects"] = ce
        
        return adapted
    
    @staticmethod
    def _sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively sanitize a dictionary to ensure JSON serializability.
        Converts complex types to simple types.
        """
        sanitized = {}
        for key, value in data.items():
            if isinstance(value, dict):
                sanitized[key] = ResultAdapter._sanitize_dict(value)
            elif isinstance(value, (list, tuple)):
                sanitized[key] = [
                    ResultAdapter._sanitize_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, (str, int, float, bool, type(None))):
                sanitized[key] = value
            else:
                # Convert unknown types to string
                sanitized[key] = str(value)
        
        return sanitized