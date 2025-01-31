from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Player:
    """Unified player representation"""
    id: Any
    name: str
    position: str
    year: int
    batting_stats: Optional[Dict]
    pitching_stats: Optional[Dict]
    
    def __init__(self, id, name, position, year, batting_stats, pitching_stats):
        self.id = id
        self.name = name
        self.position = position
        self.year = year
        self._batting_stats = batting_stats
        self._pitching_stats = pitching_stats
    
    @property
    def batting_stats(self) -> Optional[Dict]:
        """Get batting stats with proper access"""
        return self._batting_stats
    
    @property
    def pitching_stats(self) -> Optional[Dict]:
        """Get pitching stats with proper access"""
        return self._pitching_stats
    
    def __getattr__(self, item):
        """Custom attribute access that avoids recursion"""
        if self._batting_stats and item in self._batting_stats:
            return self._batting_stats[item]
        if self._pitching_stats and item in self._pitching_stats:
            return self._pitching_stats[item]
        if item == 'get':
            return lambda key, default=None: getattr(self, key, default)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")

    def get(self, key, default=None):
        """Implement dictionary-like get method for compatibility"""
        if key == 'player':
            return {
                'fullName': self.name,
                'stats': self.stats,
                'id': self.id,
                'position': self.position
            }
        return getattr(self, key, default)    
    @property
    def stats(self):
        """Get the appropriate stats object based on position"""
        return self._pitching_stats if self.position == 'P' else self._batting_stats
    
    def get_stats(self, stat_type: str) -> Dict:
        if stat_type == 'batting':
            return self._batting_stats or {}
        return self._pitching_stats or {}
        
    def to_dict(self, stat_type:str) -> Dict:
        """Convert player to dictionary format"""
        return {
            'player': {
                'id': self.id,
                'fullName': self.name,
                'position': self.position,
                'stats': self.get_stats(stat_type)
            }
        }