from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import statistics

@dataclass
class AdvancedMetrics:
    """Encapsulates advanced baseball metrics"""

    exit_velocity_metrics: Dict[str, float] = field(default_factory=dict)
    pitch_velocity_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {

            "exit_velocity_metrics": self.exit_velocity_metrics,
            "pitch_velocity_metrics": self.pitch_velocity_metrics
        }


@dataclass
class GameAtBatStats:
    """Encapsulates batting-specific statistics"""
    hits: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    rbis: int = 0
    walks: int = 0
    strikeouts: int = 0
    groundouts: int = 0
    flyouts: int = 0
    lineouts: int = 0
    exit_velocity: float = 0.0
    hit_sequence: List[Dict[str, Any]] = field(default_factory=list)
    
        
    @property
    def at_bats(self) -> int:
        total = (self.hits + self.strikeouts + self.groundouts + 
                self.flyouts + self.lineouts)
        if total > 2147483647:  # Max 32-bit integer
            raise ValueError("At-bats total exceeds maximum allowed value")
        return total

    @property
    def avg(self) -> float:
        """Calculate batting average"""
        return self.hits / self.at_bats if self.at_bats > 0 else 0.0

    
  
    
@dataclass
class GamePitchingStats:
    """Encapsulates pitching-specific statistics"""
    innings_pitched: float = 0.0
    pitches_thrown: int = 0
    fielded_out_hits: int = 0
    earned_runs: int = 0
    hits_allowed: int = 0
    strikeouts: int = 0
    total_strikeouts: int = 0
    walks: int = 0
    pitch_velocity: List[float] = field(default_factory=list)

    
    @property
    def era(self) -> float:
        """Calculate ERA"""
        return (self.earned_runs * 9) / self.innings_pitched if self.innings_pitched > 0 else 0.0
    
    @property
    def avg_pitch_velocity(self) -> float:
        """Calculate average pitch velocity"""
        return statistics.mean(self.pitch_velocity) if self.pitch_velocity else 0.0

@dataclass
class GamePlayer:
    """Represents a player in a game with their statistics"""
    player_id: int
    name: str 
    team: str
    position: str
    batting_stats: Optional[GameAtBatStats] = None
    pitching_stats: Optional[GamePitchingStats] = None

    def __post_init__(self):
        """Initialize stats objects based on position and validate data"""
        if not self.name:
            raise ValueError("Player name is required")
        if not self.team:
            raise ValueError("Team name is required")
        if not self.position:
            raise ValueError("Position is required")

        if self.position == 'DH':
            self.batting_stats = GameAtBatStats()
        elif self.position == 'P':
            self.pitching_stats = GamePitchingStats()
            if self.batting_stats is None:
                self.batting_stats = GameAtBatStats()
        else:
            self.batting_stats = GameAtBatStats()

    @property
    def pitches_thrown(self) -> int:
        """Get the total number of pitches thrown if available"""
        if self.pitching_stats:
            return self.pitching_stats.pitches_thrown
        return 0
    
    @property
    def pitch_velocity(self) -> float:
        """Get the average pitch velocity if available"""
        if self.pitching_stats:
            return self.pitching_stats.pitch_velocity
        return 0.0
    
    def validate_stats(self) -> List[str]:
        """Validate statistics for consistency"""
        errors = []
        
        if self.batting_stats:
            total_component_hits = (self.batting_stats.singles + 
                                  self.batting_stats.doubles + 
                                  self.batting_stats.triples + 
                                  self.batting_stats.home_runs)
            if total_component_hits != self.batting_stats.hits:
                errors.append(f"Hit total mismatch: {self.batting_stats.hits} vs components {total_component_hits}")

        if self.pitching_stats:
            ip_decimal = self.pitching_stats.innings_pitched % 1
            if ip_decimal not in (0.0, 0.1, 0.2):
                errors.append(f"Invalid innings pitched format: {self.pitching_stats.innings_pitched}")

        return errors

    def to_dict(self) -> Dict:
        """Convert player and stats to dictionary with validation"""
        errors = self.validate_stats()
        if errors:
            raise ValueError(f"Invalid statistics for player {self.name}: {'; '.join(errors)}")

        base_dict = {
            'player_id': self.player_id,
            'name': self.name,
            'team': self.team,
            'position': self.position
        }
        
        if self.batting_stats:
            base_dict.update({
                'batting': self.batting_stats.__dict__,
                'avg': self.batting_stats.avg,
                'exit_velocity': self.batting_stats.exit_velocity
            })
            
        if self.pitching_stats:
            base_dict.update({
                'pitching': self.pitching_stats.__dict__,
                'era': self.pitching_stats.era,
                'pitch_velocity': self.pitching_stats.pitch_velocity
            })
            
        return base_dict

    def update_batting_stats(self, new_stats: GameAtBatStats) -> None:
        """Update batting statistics with validation"""
        if self.position == 'P' and self.batting_stats is None:
            self.batting_stats = new_stats
        elif self.batting_stats is None:
            raise ValueError(f"Cannot update batting stats for player {self.name} with position {self.position}")
        else:
            self.batting_stats = new_stats

    def update_pitching_stats(self, new_stats: GamePitchingStats) -> None:
        """Update pitching statistics with validation"""
        if self.position != 'P':
            raise ValueError(f"Cannot update pitching stats for non-pitcher {self.name}")
        self.pitching_stats = new_stats

@dataclass
class PlayerPerformance:
    """Represents a player's performance in a game with advanced metrics"""
    name: str
    team: str
    score: float
    highlights: Optional[List[str]] = None
    stats: Optional[Dict] = None
    player_id: Optional[int] = None
    pitcher_score: Optional[float] = None
    advanced_metrics: Optional[AdvancedMetrics] = None

    def __post_init__(self):
        """Validate performance data"""
        if not self.name:
            raise ValueError("Player name is required")
        if self.score < 0:
            raise ValueError("Score cannot be negative")
        if self.pitcher_score is not None and self.pitcher_score < 0:
            raise ValueError("Pitcher score cannot be negative")

    @property
    def player_team(self) -> str:
        """Extract player team from stats if available"""
        if self.stats and 'team' in self.stats:
            return self.stats['team']
        return
    
    def to_dict(self) -> Dict:
        """Convert performance to dictionary with proper typing"""
        base_dict = {
            "name": self.name,
            "team": self.team,
            "score": float(self.score),  
            "highlights": self.highlights if self.highlights else None,
            "player_id": self.player_id,
            "pitcher_score": float(self.pitcher_score) if self.pitcher_score is not None else None,
            "stats": dict(self.stats) if self.stats else None  
        }
        if self.advanced_metrics:
            base_dict["advanced_metrics"] = self.advanced_metrics.to_dict()
        return base_dict

    def __json__(self):
        """JSON serialization support"""
        return self.to_dict()
        
    @classmethod
    def from_dict(cls, data: Dict) -> 'PlayerPerformance':
        """Create a PlayerPerformance instance from dictionary data"""
        advanced_metrics_data = data.pop('advanced_metrics', None)
        advanced_metrics = (
            AdvancedMetrics(**advanced_metrics_data)
            if advanced_metrics_data else None
        )
        return cls(**data, advanced_metrics=advanced_metrics)