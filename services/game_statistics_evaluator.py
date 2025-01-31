from dataclasses import dataclass, field
from typing import Dict, Optional, TypeVar, Generic, Any
from abc import ABC, abstractmethod
from services.game_statistics_models import GameAtBatStats, GamePitchingStats, GamePlayer, AdvancedMetrics, PlayerPerformance


T = TypeVar('T')  
class BaseMetric(Generic[T], ABC):
    """Base class for all performance metrics"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the metric"""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what the metric measures"""
        pass
    
    @abstractmethod
    def validate_input(self, stats: T) -> bool:
        """Validate input statistics"""
        pass
        
    @abstractmethod
    def calculate(self, stats: T) -> float:
        """Calculate the metric value"""
        pass
        
    def __call__(self, stats: T) -> Dict[str, Any]:
        """Calculate metric and return formatted result"""
        if not self.validate_input(stats):
            raise ValueError(f"{self.name} received invalid input")
            
        value = self.calculate(stats)
        return {
            "name": self.name,
            "value": value,
            "description": self.description
        }

        
@dataclass
class PerformanceConfig:
    """Configuration for performance evaluation"""
    batting_weights: Dict[str, float] = field(default_factory=lambda: {
        'hits': 2.0,
        'doubles': 1.5,
        'triples': 2.5,
        'home_runs': 4.0,
        'rbis': 1.5,
        'walks': 0.75,
        'strikeouts': -0.75
    })
    
    pitching_weights: Dict[str, float] = field(default_factory=lambda: {
        'innings_pitched': 3.0,
        'strikeouts': 2.5,
        'earned_runs': -3.0,
        'fielded_out_hits': 0.5,
        'hits_allowed': -1.5,
        'walks': -1.5
    })

class PerformanceManager:
    """Manages performance evaluation with advanced metrics"""
    
    def __init__(self, config: Optional[PerformanceConfig] = None):
        self.config = config or PerformanceConfig()

    
    def generate_highlights(self, player: GamePlayer, 
                        batting_stats: Optional[GameAtBatStats], 
                        pitching_stats: Optional[GamePitchingStats]) -> PlayerPerformance:
        """Generate highlights for a player's performance"""
        highlights = []
        
        if player.position == 'P' and pitching_stats:
            if pitching_stats.hits_allowed == 0:
                if pitching_stats.innings_pitched >= 9:
                        highlights.append(f"Threw a no-hitter over {pitching_stats.innings_pitched} innings")
                else:
                    highlights.append(f"Allowed no hits in {pitching_stats.innings_pitched} innings")
                    
            if pitching_stats.earned_runs == 0:
                if pitching_stats.innings_pitched >= 9:
                    highlights.append(f"Threw a complete game shutout")
                else:
                    highlights.append(f"Pitched {pitching_stats.innings_pitched} scoreless innings")

            # Strikeout milestones
            if pitching_stats.total_strikeouts >= 20:
                highlights.append(f"Historic {pitching_stats.total_strikeouts} strikeout performance")
            elif pitching_stats.total_strikeouts >= 15:
                highlights.append(f"Dominant {pitching_stats.total_strikeouts} strikeout performance")
            elif pitching_stats.total_strikeouts >= 10:
                highlights.append(f"Recorded {pitching_stats.total_strikeouts} strikeouts")

            # Walk and control highlights
            if pitching_stats.walks == 0 and pitching_stats.innings_pitched >= 6:
                highlights.append(f"Perfect control with no walks over {pitching_stats.innings_pitched} innings")
            
            # Pitch count efficiency
            if pitching_stats.pitches_thrown < 100 and pitching_stats.innings_pitched >= 8:
                highlights.append(f"Efficient outing with only {pitching_stats.pitches_thrown} pitches")
            
        if batting_stats:
            if batting_stats.hits >= 4:
                highlights.append(f"Outstanding {batting_stats.hits}-hit performance")
            elif batting_stats.hits >= 3:
                highlights.append(f"Collected {batting_stats.hits} hits")
            elif batting_stats.hits == 2:
                highlights.append(f"Multi-hit game")

            # Extra base hits
            if batting_stats.home_runs >= 2:
                highlights.append(f"Smashed {batting_stats.home_runs} home runs")
            elif batting_stats.home_runs == 1:
                highlights.append("Hit a home run")
                
            if batting_stats.triples >= 1:
                highlights.append(f"Hit {batting_stats.triples} triple{'s' if batting_stats.triples > 1 else ''}")
                
            if batting_stats.doubles >= 3:
                highlights.append(f"Extra-base machine with {batting_stats.doubles} doubles")
            elif batting_stats.doubles == 2:
                highlights.append("Hit two doubles")
                
            # RBI production    
            if batting_stats.rbis >= 4:
                highlights.append(f"Drove in {batting_stats.rbis} runs")
            elif batting_stats.rbis >= 2:
                highlights.append(f"Collected {batting_stats.rbis} RBI")

        return highlights
    
    
    def evaluate_batting(self, stats: Optional[GameAtBatStats]) -> Dict[str, float]:
        if stats is None or stats.at_bats == 0:
            return {
                'base_score': 0.0,
                'exit_velocity': 0.0
            }
        try:    
            base_score = sum(
                getattr(stats, stat, 0) * weight
                for stat, weight in self.config.batting_weights.items()
            )
        except Exception as e:
            base_score = 0.0
        
        return {
            'base_score': base_score,
            'exit_velocity': stats.exit_velocity
        }
        
    def evaluate_pitching(self, stats: Optional[GamePitchingStats]) -> Dict[str, float]:
        """Calculate comprehensive pitching metrics"""
        if stats is None or stats.innings_pitched == 0:
            return {
                'base_score': 0.0,
                'avg_pitch_velocity': 0.0
            }
        try:
            base_score = max(0.0, sum(
                getattr(stats, stat, 0) * weight
                for stat, weight in self.config.pitching_weights.items()
            ))
        except Exception as e:
            base_score = 0.0
        
        return {
            'base_score': base_score,
            'avg_pitch_velocity': stats.avg_pitch_velocity
        }

    def evaluate_player(self, player: GamePlayer) -> Optional[PlayerPerformance]:
        """Evaluate player with advanced metrics"""
        if not player:
            return None
            
        advanced_metrics = AdvancedMetrics()
        score = 0.0
        pitcher_score = None
        stats = {}
        highlights = []
        
        if player.batting_stats:
            batting_metrics = self.evaluate_batting(player.batting_stats)
            batting_highlights = self.generate_highlights(player, player.batting_stats, None)
            score = max(0.0, batting_metrics['base_score'])
            
            if player.batting_stats.exit_velocity > 0:
                advanced_metrics.exit_velocity_metrics = player.batting_stats.exit_velocity,

            stats['batting'] = player.batting_stats.__dict__
            highlights.extend(batting_highlights)
            
        if player.pitching_stats:
            pitching_metrics = self.evaluate_pitching(player.pitching_stats)
            pitching_highlights = self.generate_highlights(player, None, player.pitching_stats)
            pitcher_score = max(0.0, pitching_metrics['base_score'])
            
            if player.pitching_stats.pitch_velocity:
                advanced_metrics.pitch_velocity_metrics = {
                    'avg': pitching_metrics['avg_pitch_velocity'],
                    'max': max(player.pitching_stats.pitch_velocity),
                    'min': min(player.pitching_stats.pitch_velocity)
                }
            stats['pitching'] = player.pitching_stats.__dict__
            highlights.extend(pitching_highlights)

        return PlayerPerformance(
            name=player.name,
            team=player.team,
            score=score,
            highlights=highlights,
            pitcher_score=pitcher_score,
            stats=stats,
            advanced_metrics=advanced_metrics,
            player_id=player.player_id
        )