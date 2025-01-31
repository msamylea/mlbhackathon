from typing import List, Tuple
from manager.batting_results import AtBatResult
from manager.base_running import BaseState, BaseRunningManager
from manager.roster_manager import TeamManager, TeamRoster
from manager.player_manager import Player
from stats.centralized_stats import CentralizedStatsService
from data.data_loader import TeamDataLoader
import traceback

class GameState:
    def __init__(self, away_team_data: TeamRoster, home_team_data: TeamRoster, stats_service: CentralizedStatsService):
        self.data_loader = TeamDataLoader()
        self.stats_service = stats_service
        
        self.venue = None
        self.inning = 1
        self.top_of_inning = True
        self.outs = 0
        self.bases = BaseState()
        self.scored_runners = []
        self.pitch_sequence = []
        self._current_batter_cache = None
        self._current_pitcher_cache = None
        self._scored_runners_cache = []
        self.team_manager = TeamManager(away_team_data, home_team_data)
  
        self.home_year = home_team_data.year
        self.batting_order = self.current_batting_order
    
        self.final_score = None
        self.score = {
            self.team_manager.away_team.name: 0,
            self.team_manager.home_team.name: 0
        }
        
        
        self.max_regulation_innings = 2 
        self.max_extra_innings = 2     
        self.max_innings = self.max_regulation_innings
        

    def __get__(self, item):
        return getattr(self, item)
    
    @property
    def pitch_arsenal(self):
        return self.team_manager.get_current_pitch_arsenal()    
    @property
    def batting_team(self) -> 'TeamRoster':
        """Get current batting team"""
        return self.team_manager.batting_team
    
    @property
    def fielding_team(self) -> 'TeamRoster':
        """Get current fielding team"""
        return self.team_manager.fielding_team
    
           
    
    
    @property
    def current_batting_order(self) -> TeamRoster:
        """Get current batting order based on inning state"""
        if self.top_of_inning:
            self.away_is_batting = True
        else:
            self.away_is_batting = False
        self.team_manager._away_is_batting = self.away_is_batting
        self.batting_order =self.team_manager.batting_team._batter_lineup
        return self.batting_order
    
    def _clear_cached_runners(self):
        """Clear the scored runners cache"""
        self._scored_runners_caches = []
            
    def _clear_player_cache(self):
        """Clear the cached batter and pitcher when changing innings or advancing batters"""
        self._current_batter_cache = None
        self._current_pitcher_cache = None
        
    def get_batting_lineup(self):
        """Get current batting team's lineup"""
        return self.current_batting_order
    
    def get_current_batter(self) -> Player:
        """Get current batter with cached stats"""
        try:
            if self._current_batter_cache is None:
                batter = self.team_manager.get_current_batter()
                if isinstance(batter, Player):
                    self._current_batter_cache = batter  
                else:
                    player_data = batter.get('player', {})
                    self._current_batter_cache = Player(
                        id=player_data.get('id'),
                        name=player_data.get('fullName'),
                        position=player_data.get('position'),
                        year=self.inning,
                        batting_stats=self.stats_service.process_player_stats(batter, self.inning),
                        pitching_stats=None
                    )
        except Exception as e:
            raise e
     
        return self._current_batter_cache

    
    def get_current_pitcher(self) -> Player:
        """Get current pitcher with cached stats"""
        try:
            if self._current_pitcher_cache is None:
                pitcher_dict = self.team_manager.get_current_pitcher()
                if isinstance(pitcher_dict, dict):
                    player_data = pitcher_dict.get('player', {})
                    self._current_pitcher_cache = Player(
                        id=player_data.get('id'),
                        name=player_data.get('fullName'),
                        position=player_data.get('position'),
                        year=self.inning,  
                        batting_stats=None,
                        pitching_stats=player_data.get('stats', {})
                    )
                else:
                    self._current_pitcher_cache = pitcher_dict
        except Exception as e:
            raise e
        return self._current_pitcher_cache

    def get_current_defense(self):
        """Get current fielding team's defensive alignment"""
        return self.fielding_team._defense if self.fielding_team else []

    def update(self, play_result: AtBatResult) -> Tuple[str, int]:
        try:
            self._clear_cached_runners()
            self.current_batter = play_result.batter_name

            self.current_batter_stats = play_result.batter_stats
            initial_outs = self.outs
    
            if play_result.final_fielded_out in ['grounds out', 'flies out', 'lines out']:
                play_result.final_result = 'fielded out'
    
            if play_result.final_result == 'strikeout':
                self.outs += 1
            elif play_result.final_result == 'fielded out':
                self.outs += 1
    
            will_end_inning = (initial_outs == 2 and play_result.final_result in ['fielded out', 'strikeout'])

            base_movers = ''
            base_movement_actions = ['singles', 'doubles', 'triples', 'hits a home run']
            if play_result.final_hit in base_movement_actions:
                base_movers = play_result.final_hit
                
            walk = 'walk' if play_result.final_result == 'walk' else ''

            if self.outs < 3:
                advancement, scored_runners = BaseRunningManager.determine_advancement(
                    play_type=base_movers if base_movers else walk,
                    base_state=self.bases,
                    outs=self.outs
                    )
    
                if self.bases is None:
                    self.bases = BaseState()
    
                self.bases = BaseRunningManager.update_base_state(
                    current_state=self.bases,
                    batter_name=self.current_batter,
                    advancement=advancement,
                    scored_runners=scored_runners
                )
                
                if scored_runners:
                    scored_runners = list(set(scored_runners))  
                    play_result.add_scored_runners(scored_runners)
                    self.scored_runners = scored_runners
                    self.score[self.batting_team.name] += len(scored_runners)
    
            self.batter_stats = play_result.batter_stats
            self.pitcher_stats = play_result.pitcher_stats
            self.pitch_sequence = play_result.pitch_sequence.copy()
            self._scored_runners_cache = self.scored_runners.copy()

            self._clear_player_cache()
            next_batter = self.team_manager.advance_batter()
            if next_batter:
                self.current_batter = next_batter.get('player', {}).get('fullName')
            result = str(play_result)
            self.scored_runners = []
    
            final_outs = self.outs
            if will_end_inning:
                final_outs = 3
                self._next_half_inning()
            elif self.outs >= 3:
                self._next_half_inning()
    
            return result, final_outs
    
        except Exception as e:
            raise e
        
    def _next_half_inning(self) -> None:
        """Handle transition to next half-inning"""
        self.outs = 0
        self.bases = BaseState()
        self._clear_player_cache()
    
        if self.top_of_inning:
            self.top_of_inning = False
        else:
            self.top_of_inning = True
            self.inning += 1
            
        # Switch teams in manager
        self.team_manager.switch_teams()
        
    def is_game_over(self) -> bool:
        if self.inning >= self.max_regulation_innings + self.max_extra_innings:
            return True

        if self.inning < self.max_regulation_innings:
            return False

        if not self.top_of_inning:
            if self.is_home_team_ahead():
                return True
            if self.is_tied() and self.outs < 3:
                return False
            if self.is_tied() and self.outs >= 3:
                if self.inning < self.max_regulation_innings + self.max_extra_innings:
                    self.max_innings += 1  
                    return False
                return True  
            
        else:
            if self.outs >= 3 and self.is_home_team_ahead():
                return True
            return False

        return False
    
    
    def is_tied(self) -> bool:
        return self.score[self.team_manager.home_team.name] == self.score[self.team_manager.away_team.name]
    
    def is_home_team_ahead(self) -> bool:
        return self.score[self.team_manager.home_team.name] > self.score[self.team_manager.away_team.name]
   
    def _format_base_state(self) -> List[str]:
        """Format current base state for display"""
        base_list = []
        base_names = ['first', 'second', 'third']
        
        for i, base in enumerate(self.bases._bases):
            if base:
                base_list.append(f"{base} on {base_names[i]}")
        
        return base_list if base_list else []
    @property
    def current_score(self) -> str:
        """Get formatted current score"""
        return (f"{self.team_manager.away_team.name}: {self.score[self.team_manager.away_team.name]}, "
                f"{self.team_manager.home_team.name}: {self.score[self.team_manager.home_team.name]}")