from dataclasses import dataclass, field
from typing import Dict, List, Union
from manager.player_manager import Player
from stats.base_stats import PitchArsenal

@dataclass
class TeamIdentifier:
    """Uniquely identifies a team including its year"""
    name: str
    year: int

    def __str__(self) -> str:
        return f"{self.name} ({self.year})"

    def as_key(self) -> str:
        """Creates a unique key for dictionary storage"""
        return f"{self.name}_{self.year}"


@dataclass
class TeamRoster:
    def __init__(self, id, name, year, _current_batter_index, roster, starting_pitcher, pitch_arsenal, _batter_lineup, _defense):
        self.id = id
        self.name = name
        self.year = year
        self._current_batter_index = _current_batter_index
        self.roster = roster
        self.starting_pitcher = starting_pitcher
        self.pitch_arsenal = pitch_arsenal
        self._batter_lineup = _batter_lineup 
        self._defense = _defense

    def __len__(self):
        return len(self._batter_lineup)
    
    @property 
    def defense(self) -> List[Dict]:
        return self._defense

    def get_defensive_alignment(self) -> List[Dict]:
        """Return defensive alignment"""
        
        return self.defense
    
    def get_pitch_arsenal(self) -> Dict:
        """Get pitcher's arsenal with validation"""
        if not self.pitch_arsenal:
            return PitchArsenal.get_default_arsenal()
            
        if isinstance(self.pitch_arsenal, dict):
            return self.pitch_arsenal
            
        return {
            'pitches': {
                'FF': {
                    'code': 'FF',
                    'name': 'Four-Seam Fastball', 
                    'percentage': 50.0,
                    'avg_speed': 93.5
                },
                'SL': {
                    'code': 'SL',
                    'name': 'Slider',
                    'percentage': 20.0,
                    'avg_speed': 85.0
                },
                'CH': {
                    'code': 'CH', 
                    'name': 'Changeup',
                    'percentage': 15.0,
                    'avg_speed': 83.0
                },
                'CU': {
                    'code': 'CU',
                    'name': 'Curveball', 
                    'percentage': 15.0,
                    'avg_speed': 78.0
                }
            },
            'primary_pitch': 'FF'
        }

    def get_lineup_positions(self) -> Dict[str, str]:
        """Get defensive positions for lineup"""
        return {
            player.name: player.position
            for player in self.roster
        }
        
    @property
    def current_batter(self) -> Player:
        """Get current batter in lineup"""
        if not self._batter_lineup:
            raise ValueError("No batters in lineup")
        return self._batter_lineup[self._current_batter_index]

    def advance_batter(self) -> Player:
        """Move to next batter in lineup"""
        if not self._batter_lineup:
            raise ValueError("No players in lineup")
        self._current_batter_index = (self._current_batter_index + 1) % len(self._batter_lineup)
        return self.current_batter
    
    def get_stats(self, player: Player, stat_type: str) -> Dict:
        """Single method for getting any player stats"""
        return player.get_stats(stat_type)
    
    def current_pitcher(self) -> Player:
        """Get current pitcher in lineup"""
        return self.starting_pitcher

    

@dataclass
class TeamManager:
    """Manages game state for both teams"""
    away_team: TeamRoster
    home_team: TeamRoster
    _away_is_batting: bool = True
    _current_batter_index: int = field(default=0, init=False)
        
    @property
    def batting_team(self) -> TeamRoster:
        """Get current batting team"""
        return self.away_team if self._away_is_batting else self.home_team

    @property
    def fielding_team(self) -> TeamRoster:
        """Get current fielding team"""
        return self.home_team if self._away_is_batting else self.away_team
    
    @property
    def batter_lineup(self) -> List[Player]:
        return self.batting_team._batter_lineup

    def get_current_batter(self) -> Player:
        batter = self.batting_team._batter_lineup[self._current_batter_index]
        return self._ensure_player(batter)
        
    def _ensure_player(self, data: Union[Player, Dict]) -> Player:
        if isinstance(data, Player):
            return data
        player_data = data.get('player', {})
        return Player(
            id=player_data.get('id'),
            name=player_data.get('fullName'),
            position=player_data.get('position'),
            year=self.batting_team.year,
            batting_stats=player_data.get('stats'),
            pitching_stats=None
        )

    def get_current_pitcher(self) -> Player:
        """Single source of truth for current pitcher"""
        return self.fielding_team.starting_pitcher

    def advance_batter(self) -> Player:
        """Move to next batter with validation"""
        lineup = self.batting_team._batter_lineup
        if not lineup:
            raise ValueError("No batting lineup available")

        self._current_batter_index = (self._current_batter_index + 1) % len(lineup)
        return self.get_current_batter()

    def get_defensive_positions(self) -> List[Dict]:
        """Get current defensive alignment"""
        return self.fielding_team.get_defensive_alignment()

    def get_current_pitch_arsenal(self) -> Dict:
        """Get current pitcher's arsenal"""
            
        arsenal = self.fielding_team.get_pitch_arsenal()
       
        return arsenal

    def switch_teams(self) -> None:
        if self._away_is_batting:
            self.away_team._current_batter_index = self._current_batter_index
            self._away_is_batting = False
            self._current_batter_index = self.home_team._current_batter_index
        else:
            self.home_team._current_batter_index = self._current_batter_index
            self._away_is_batting = True
            self._current_batter_index = self.away_team._current_batter_index