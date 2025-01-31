from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import json
from services.game_statistics_models import GamePlayer
from services.game_statistics_evaluator import PlayerPerformance, PerformanceConfig, PerformanceManager
from services.game_statistics_tracker import BattingStatsTracker, PitchingStatsTracker
from services.game_analysis import LLMGameAnalysis

@dataclass
class GameSummary:
    """Enhanced game summary with comprehensive validation"""
    game_info: Dict
    notable_performances: List[PlayerPerformance] = field(default_factory=list)
    mvp: Optional[PlayerPerformance] = None
    top_pitcher: Optional[PlayerPerformance] = None

    def __post_init__(self):
        """Validate required game information"""
        self._validate_game_info()

    def _validate_game_info(self) -> None:
        """Validate completeness and correctness of game information"""
        required_fields = {
            'home_team': str,
            'away_team': str,
            'final_score': dict,
            'innings_played': (int, float)
        }
        
        for field_name, expected_type in required_fields.items():
            if field_name not in self.game_info:
                raise ValueError(f"Missing required field: {field_name}")
            if not isinstance(self.game_info[field_name], expected_type):
                raise TypeError(f"Invalid type for {field_name}. Expected {expected_type}")
                
        # Validate final score
        final_score = self.game_info['final_score']
        if self.home_team not in final_score or self.away_team not in final_score:
            raise ValueError("Final score must include both home and away teams")
        
        for team, score in final_score.items():
            if not isinstance(score, int) or score < 0:
                raise ValueError(f"Invalid score for {team}: {score}")
                
        # Validate innings played
        innings = self.game_info['innings_played']
        if innings < 1:
            raise ValueError(f"Invalid number of innings: {innings}")

    @property
    def home_team(self) -> str:
        return self.game_info['home_team']
    
    @property
    def away_team(self) -> str:
        return self.game_info['away_team']
    
    @property
    def final_score(self) -> Dict[str, int]:
        return self.game_info['final_score']
    
    @property
    def innings_played(self) -> int:
        return self.game_info['innings_played']
    
    @property
    def winner(self) -> Optional[str]:
        scores = list(self.final_score.items())
        if scores[0][1] == scores[1][1]:
            return None
        return max(scores, key=lambda x: x[1])[0]

    @property
    def loser(self) -> Optional[str]:
        scores = list(self.final_score.items())
        if scores[0][1] == scores[1][1]:
            return None
        return min(scores, key=lambda x: x[1])[0]
    
    @property
    def winning_score(self) -> Optional[int]:
        if self.winner is None:
            return None
        return self.final_score[self.winner]

    @property
    def losing_score(self) -> Optional[int]:
        if self.loser is None:
            return None
        return self.final_score[self.loser]

    
    def add_performance(self, performance: PlayerPerformance, is_pitcher: bool = False) -> None:
        """Add a performance with validation"""
        if not isinstance(performance, PlayerPerformance):
            raise TypeError("Performance must be a PlayerPerformance instance")
        
        self.notable_performances.append(performance)
        
        if is_pitcher and (self.top_pitcher is None or 
                          performance.pitcher_score > self.top_pitcher.pitcher_score):
            self.top_pitcher = performance
        elif not is_pitcher and (self.mvp is None or performance.score > self.mvp.score):
            self.mvp = performance

    def to_dict(self) -> Dict:
        """Convert to dictionary with complete details"""
        return {
            "game_info": {
                **self.game_info,
                "winner": self.winner,
                "loser": self.loser,
                "winning_score": self.winning_score,
                "losing_score": self.losing_score
            },
            "mvp": self._performance_to_dict(self.mvp) if self.mvp else None,
            "top_pitcher": self._performance_to_dict(self.top_pitcher) if self.top_pitcher else None,
            "notable_performances": [self._performance_to_dict(perf) for perf in self.notable_performances],
        }

    def _performance_to_dict(self, perf: PlayerPerformance) -> Dict:
        """Convert performance to dictionary with complete metrics"""
        return {
            "name": perf.name,
            "team": perf.team,
            "score": perf.score,
            "highlights": perf.highlights,
            "pitcher_score": perf.pitcher_score,
            "player_id": perf.player_id,
            "advanced_metrics": perf.advanced_metrics.to_dict() if perf.advanced_metrics else None
        }
            
class GameStatsManager:
    """Main class for managing game statistics"""
    
    REQUIRED_FIELDS = {
        'batting': ['batter_name', 'batter_id', 'batter_position', 'batting_team'],
        'pitching': ['pitcher_name', 'pitcher_id', 'fielding_team']
    }
    
    def __init__(self, home_team: str, away_team: str, config: Optional[PerformanceConfig] = None):
        self.home_team = home_team
        self.away_team = away_team
        self.players: Dict[str, GamePlayer] = {}
        self.game_highlights: List[str] = []
        self.performance_manager = PerformanceManager(config)
        self.batting_stats_tracker = BattingStatsTracker()
        self.pitching_stats_tracker = PitchingStatsTracker()
        self.client = None
    
    def get_game_leaders(self) -> Dict[str, PlayerPerformance]:
        performances = []
        pitcher_performances = []
        
        for player in self.players.values():
            perf = self.performance_manager.evaluate_player(player)
            if not perf:
                continue

            if player.position == 'P' and player.pitching_stats:
                highlights = self.performance_manager.generate_highlights(
                    player=player,
                    batting_stats=None,
                    pitching_stats=player.pitching_stats,
                )
                if highlights:
                    perf.highlights = highlights  # Set highlights on performance
                pitcher_performances.append(perf)
            elif player.batting_stats:
                highlights = self.performance_manager.generate_highlights(
                    player=player,
                    batting_stats=player.batting_stats,
                    pitching_stats=None,
                )
                if highlights:
                    perf.highlights = highlights  # Set highlights on performance
                performances.append(perf)
                        
        result = {}
        if performances:
            result['mvp'] = max(performances, key=lambda x: x.score)
            result['notable'] = sorted(performances, key=lambda x: x.score, reverse=True)[:3]
        if pitcher_performances:
            result['top_pitcher'] = max(
                pitcher_performances, 
                key=lambda x: x.pitcher_score if x.pitcher_score is not None else float('-inf')
            )
                
        return result

    def _validate_play_data(self, play_data: Dict) -> None:
        is_pitcher = play_data.get('position') == 'P'
        required = self.REQUIRED_FIELDS['pitching' if is_pitcher else 'batting']
        
        missing = [field for field in required if not play_data.get(field)]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")
    
    def _get_player_key(self, name: str, team: str) -> str:
            return f"{name}_{team}"

    def _get_or_create_player(self, play_data: Dict) -> GamePlayer:
        is_pitcher = play_data.get('position') == 'P'
        
        if is_pitcher:
            player_name = play_data.get('pitcher_name')
            team = play_data.get('fielding_team')
            player_id = play_data.get('pitcher_id', 0)
            player_position = 'P'
        else:
            player_name = play_data.get('batter_name')
            team = play_data.get('batting_team')
            player_id = play_data.get('batter_id', 0)
            player_position = play_data.get('batter_position', '')

        player_key = f"{player_name}_{team}_{player_position}"
        
        if player_key not in self.players:
            player = GamePlayer(
                player_id=player_id,
                name=player_name,
                team=team,
                position=player_position
            )
            self.players[player_key] = player
            
        return self.players[player_key]
    
    def record_play(self, play_data: Dict) -> None:
        try:
            # First handle pitching stats
            pitcher_data = {
                **play_data,
                'position': 'P'
            }
            self._validate_play_data(pitcher_data)
            pitcher = self._get_or_create_player(pitcher_data)
            pitcher_stats = self.pitching_stats_tracker.update_stats(
                pitcher.pitching_stats,
                play_data
            )
            pitcher.update_pitching_stats(pitcher_stats)
    
            # Then handle batting stats separately
            batter_data = {
                **play_data,
                'position': play_data.get('batter_position', '')
            }
            
            self._validate_play_data(batter_data)
            batter = self._get_or_create_player(batter_data)
            batter_stats = self.batting_stats_tracker.update_stats(
                batter.batting_stats,
                play_data
            )
            batter.update_batting_stats(batter_stats)
    
        except Exception as e:
            raise ValueError(f"Error recording play: {str(e)}")

    def determine_game_outcome(self, final_score: Dict[str, int]) -> Dict[str, Optional[str]]:
        """Determine game outcome with proper tie handling"""
        teams = list(final_score.items())
        if len(teams) != 2:
            raise ValueError("Final score must have exactly two teams")
            
        if teams[0][1] == teams[1][1]:
            return {
                "winner": None,
                "loser": None,
                "tie": True
            }
        
        winner = max(teams, key=lambda x: x[1])
        loser = min(teams, key=lambda x: x[1])
        return {
            "winner": winner[0],
            "loser": loser[0],
            "tie": False
        }    
        
    def generate_summary(self, final_score: Dict[str, int], innings_played: int) -> Tuple[GameSummary, Optional[str]]:
        """Generate enhanced game summary with advanced metrics and optional LLM analysis"""
        summary = self._generate_base_summary(final_score, innings_played)
        
        # Generate LLM analysis if client is available
        llm_analysis = None
            
        analyzer = LLMGameAnalysis(
            players=list(self.players.values()),
            game_info=summary,
            client = self.client
        )
        
        llm_analysis = analyzer.send_to_llm()
        
                    
        return summary, llm_analysis
        
    def _generate_base_summary(self, final_score: Dict[str, int], innings_played: int) -> GameSummary:
        game_outcome = self.determine_game_outcome(final_score)
        game_info = {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "final_score": final_score,
            "innings_played": innings_played,
            "winner": game_outcome['winner'],
            "loser": game_outcome['loser'],
            "is_tie": game_outcome['tie']
        }
                
        leaders = self.get_game_leaders()

                       
        return GameSummary(
            game_info=game_info,
            mvp=leaders.get('mvp'),
            top_pitcher=leaders.get('top_pitcher'),
            notable_performances=leaders.get('notable', []),
        )   
    