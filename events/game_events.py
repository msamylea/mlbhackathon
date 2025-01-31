from dataclasses import dataclass
from typing import Dict, List, Callable, Any
from datetime import datetime

@dataclass
class PlayResult:
    """Standardized play result information"""
    batter_name: str
    pitcher_name: str
    action: str
    location: str
    quality: str = "medium"
    exit_velocity: int = 85
    base_runners: List[str] = None
    scored_runners: List[str] = None
    defensive_play: Dict = None
    description: str = None

    def format_for_display(self) -> Dict:
        """Format play result for frontend display"""
        return {
            'batter': self.batter_name,
            'pitcher': self.pitcher_name,
            'action': self.action,
            'location': self.location,
            'quality': self.quality,
            'exit_velocity': self.exit_velocity,
            'base_runners': self.base_runners or [],
            'scored_runners': self.scored_runners or [],
            'defensive_play': self.defensive_play,
            'description': self.description
        }

        
@dataclass
class GameEvent:
    """Base class for game events"""
    type: str
    timestamp: datetime
    data: Dict[str, Any]

class EventManager:
    """Manages game events and observers with type safety"""
    def __init__(self):
        self.observers: Dict[str, List[Callable]] = {}
        self.current_game_state: Dict = {
            'inning': 1,
            'outs': 0,
            'score': {},
            'base_state': []
        }
        self._subscribers: Dict[str, List[Callable]] = {}
        
    def subscribe(self, event_type: str, callback: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        
    def emit(self, event_type: str, data: Dict) -> None:
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    raise RuntimeError(f"Error in event callback: {e}")
                    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type] 
                if cb != callback
            ]
