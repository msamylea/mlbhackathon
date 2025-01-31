import json
from typing import Dict, Any
from dataclasses import asdict, is_dataclass
from manager.batting_results import AtBatResult

class GameObjectEncoder(json.JSONEncoder):
    """Custom JSON encoder for game-related objects"""
    
    def default(self, obj):
        if is_dataclass(obj):
            return self._serialize_dataclass(obj)
            
        if isinstance(obj, AtBatResult):
            return self._serialize_at_bat_result(obj)
              
        return super().default(obj)
        
    def _serialize_dataclass(self, obj: Any) -> Dict:
        """Convert a dataclass instance to a dictionary"""
        return {k: self._handle_value(v) for k, v in asdict(obj).items()}
        
    def _serialize_at_bat_result(self, result: AtBatResult) -> Dict:
        """Convert AtBatResult to JSON-serializable dictionary"""
        return {
            'batter_stats': result.batter_stats,
            'pitcher_stats': result.pitcher_stats,
            'pitch_sequence': result.pitch_sequence,
            'scored_runners': result.scored_runners,
            'error': result.error,
            'error_description': result.error_description,
            'pitch_details': result.pitch_details,
            'final_result': result.final_result,
            'final_hit': result.final_hit,
            'final_fielded_out': result.final_fielded_out,
            'final_rationale': result.final_rationale,
            'final_pitch': result.final_pitch,
            'final_pitch_velocity': result.final_pitch_velocity,
            'final_exit_velocity': result.final_exit_velocity,
            'final_distance': result.final_distance,
            'final_location': result.final_location,
            'pitch_count': result.pitch_count,
            }
        
        
    def _handle_value(self, value: Any) -> Any:
        """Handle nested objects during serialization"""
        if is_dataclass(value):
            return self._serialize_dataclass(value)
        if isinstance(value, list):
            return [self._handle_value(item) for item in value]
        if isinstance(value, dict):
            return {k: self._handle_value(v) for k, v in value.items()}
        return value

def serialize_game_object(obj: Any) -> str:
    """Helper function to serialize game objects to JSON string"""
    return json.dumps(obj, cls=GameObjectEncoder)

def serialize_game_object_to_dict(obj: Any) -> Dict:
    """Helper function to serialize game objects to dictionary"""
    return json.loads(serialize_game_object(obj))
