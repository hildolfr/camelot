"""
Adapter to handle various return formats from poker_knight module.
This ensures consistent API responses regardless of poker_knight version changes.
"""

from typing import Dict, Any, Tuple, Optional, Union
import numpy as np


class ResultAdapter:
    """Adapts poker_knight results to consistent API format."""
    
    @staticmethod
    def convert_numpy_types(obj: Any) -> Any:
        """
        Recursively convert numpy types to Python native types for JSON serialization.
        """
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: ResultAdapter.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [ResultAdapter.convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    @staticmethod
    def normalize_confidence_interval(value: Any) -> Tuple[float, float]:
        """Convert confidence interval to tuple format."""
        if isinstance(value, tuple) and len(value) == 2:
            # Convert numpy types if present
            return (ResultAdapter.convert_numpy_types(value[0]), 
                    ResultAdapter.convert_numpy_types(value[1]))
        elif isinstance(value, list) and len(value) == 2:
            # Convert numpy types if present
            return (ResultAdapter.convert_numpy_types(value[0]), 
                    ResultAdapter.convert_numpy_types(value[1]))
        elif isinstance(value, dict):
            # Handle dict format with 'low'/'high' or 'lower'/'upper' keys
            if 'low' in value and 'high' in value:
                return (ResultAdapter.convert_numpy_types(value['low']), 
                        ResultAdapter.convert_numpy_types(value['high']))
            elif 'lower' in value and 'upper' in value:
                return (ResultAdapter.convert_numpy_types(value['lower']), 
                        ResultAdapter.convert_numpy_types(value['upper']))
        
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
            # Map actual_simulations to simulations_run for compatibility
            "simulations_run": getattr(result, 'actual_simulations', getattr(result, 'simulations_run', 0)),
            "actual_simulations": getattr(result, 'actual_simulations', 0),
            "execution_time_ms": getattr(result, 'execution_time_ms', 0.0),
            "execution_time_start": getattr(result, 'execution_time_start', None),
            "execution_time_end": getattr(result, 'execution_time_end', None),
        }
        
        # Handle confidence interval
        confidence_interval = getattr(result, 'confidence_interval', None)
        adapted["confidence_interval"] = ResultAdapter.normalize_confidence_interval(confidence_interval)
        
        # Handle hand categories (might be dict or missing)
        hand_categories = getattr(result, 'hand_category_frequencies', {})
        if hand_categories is None:
            hand_categories = {}
        # Convert numpy types to native Python types for JSON serialization
        adapted["hand_categories"] = ResultAdapter.convert_numpy_types(hand_categories)
        
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
        
        # Stack-to-Pot Ratio
        if hasattr(result, 'stack_to_pot_ratio'):
            adapted["stack_to_pot_ratio"] = getattr(result, 'stack_to_pot_ratio')
        
        # Tournament pressure
        if hasattr(result, 'tournament_pressure'):
            tp = getattr(result, 'tournament_pressure')
            if isinstance(tp, dict):
                adapted["tournament_pressure"] = tp
        
        # Fold equity estimates
        if hasattr(result, 'fold_equity_estimates'):
            fee = getattr(result, 'fold_equity_estimates')
            if isinstance(fee, dict):
                adapted["fold_equity_estimates"] = fee
        
        # Bubble factor
        if hasattr(result, 'bubble_factor'):
            adapted["bubble_factor"] = getattr(result, 'bubble_factor')
        
        # Bluff catching frequency
        if hasattr(result, 'bluff_catching_frequency'):
            adapted["bluff_catching_frequency"] = getattr(result, 'bluff_catching_frequency')
        
        # No longer tracking GPU/CPU backend - only fresh vs cached matters
        
        # Add new advanced analysis fields from poker_knightNG
        
        # SPR and betting analysis
        if hasattr(result, 'spr'):
            adapted["spr"] = getattr(result, 'spr')
        if hasattr(result, 'pot_odds'):
            adapted["pot_odds"] = getattr(result, 'pot_odds')
        if hasattr(result, 'mdf'):
            adapted["mdf"] = getattr(result, 'mdf')
        if hasattr(result, 'equity_needed'):
            adapted["equity_needed"] = getattr(result, 'equity_needed')
        if hasattr(result, 'commitment_threshold'):
            adapted["commitment_threshold"] = getattr(result, 'commitment_threshold')
        
        # Board analysis
        if hasattr(result, 'nuts_possible'):
            nuts = getattr(result, 'nuts_possible')
            if isinstance(nuts, list):
                adapted["nuts_possible"] = nuts
        if hasattr(result, 'draw_combinations'):
            draws = getattr(result, 'draw_combinations')
            if isinstance(draws, dict):
                adapted["draw_combinations"] = ResultAdapter.convert_numpy_types(draws)
        if hasattr(result, 'board_texture_score'):
            adapted["board_texture_score"] = getattr(result, 'board_texture_score')
        
        # Range analysis
        if hasattr(result, 'equity_vs_range_percentiles'):
            evr = getattr(result, 'equity_vs_range_percentiles')
            if isinstance(evr, dict):
                adapted["equity_vs_range_percentiles"] = ResultAdapter.convert_numpy_types(evr)
        if hasattr(result, 'range_coordination_score'):
            adapted["range_coordination_score"] = getattr(result, 'range_coordination_score')
        
        # Positional analysis
        if hasattr(result, 'positional_advantage_score'):
            adapted["positional_advantage_score"] = getattr(result, 'positional_advantage_score')
        
        # Hand analysis
        if hasattr(result, 'hand_vulnerability'):
            adapted["hand_vulnerability"] = getattr(result, 'hand_vulnerability')
        
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