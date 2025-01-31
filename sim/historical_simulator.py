from typing import Dict, List
from dataclasses import dataclass
from data.data_loader import TeamDataLoader
from sim.game_state import GameState
from stats.centralized_stats import CentralizedStatsService
from sim.simulator import EnhancedGameSimulator
from services.team_creation_service import TeamCreationService
from services.game_statistics_summary import GameStatsManager
from calculations.venue_data import VenueData
from events.game_events import EventManager
from utils.gemini_config import get_llm
import traceback
from time import sleep

@dataclass
class InningPlays:
    """Represents plays for a single inning"""
    inning: int
    top: bool
    plays: List[str]
    score: Dict[str, int]

@dataclass
class MatchupResult:
    """Structured result of a historical matchup simulation"""
    teams: Dict
    final_score: Dict
    innings: int
    plays: List[InningPlays]

    
class HistoricalMatchupSimulator:
    """Simulates matchups between historical MLB teams"""
    
    def __init__(self):
        self.team_data_loader = TeamDataLoader()
        self.stats_service = CentralizedStatsService() 
        self.game_simulator = EnhancedGameSimulator(self.stats_service)
        self.team_creation_service = TeamCreationService(self.team_data_loader, self.stats_service)
        self.event_manager = EventManager()
        

    def initialize_game(self, away_team: int, away_year: int, home_team: int, home_year: int, team1_name: str, team2_name: str) -> GameState:
        """Set up initial game state with cached stats"""
        try:
            away_id = away_team
            home_id = home_team
            
            away_data = self.team_data_loader.load_complete_team_data(away_team, away_year)
            home_data = self.team_data_loader.load_complete_team_data(home_team, home_year)
            
            venue_data = self.team_data_loader.get_venue_data(home_team, home_year)

            venue_details = VenueData.from_api_response(venue_data)
            
            if not away_data or not home_data:
                raise ValueError("Could not find team data")

            away_team = self.team_creation_service.create_team(away_id, away_data, away_year, team1_name)
            home_team = self.team_creation_service.create_team(home_id, home_data, home_year, team2_name)
                 
            game_state = GameState(away_team, home_team, self.stats_service)
            game_state.venue = venue_details
            
            return game_state
            
        except Exception as e:
            raise ValueError(f"Error initializing game: {str(e)}")

    def simulate_matchup(self, team1_id: int, year1: int, team2_id: int, year2: int, team1_name: str, team2_name: str, api_key: str = None) -> Dict:
        try:
            game_stats_manager = GameStatsManager(home_team=team2_name, away_team=team1_name)

            game_state = self.initialize_game(team1_id, year1, team2_id, year2, team1_name, team2_name)

            while not game_state.is_game_over():
                current_batter = game_state.get_current_batter()
                current_pitcher = game_state.get_current_pitcher()
                
                batter_stats = game_state.batting_team.get_stats(current_batter, 'batting')
                pitcher_stats = game_state.fielding_team.get_stats(current_pitcher, 'pitching')
                pitcher_df, batter_df = self.stats_service.get_formatted_stat_tables(
                    batter_stats, 
                    pitcher_stats
                )
                
                
                
                play_result = self.game_simulator.simulate_at_bat(
                    current_batter,
                    current_pitcher,
                    game_state,
                    batter_stats,
                    pitcher_stats,
                    year1,
                    year2,
                )
                play_result.batter_df = batter_df
                play_result.pitcher_df = pitcher_df

                play_details = {
                    'inning': game_state.inning,
                    'top_of_inning': game_state.top_of_inning,
                    'outs': game_state.outs,
                    'base_state': game_state._format_base_state(),
                    'pitch_sequence': play_result.pitch_sequence,
                    'batting_team_name': game_state.batting_team.name,
                    'fielding_team_name': game_state.fielding_team.name,
                    'batting_team_lineup': game_state.get_batting_lineup(),
                    'fielding_team_lineup': game_state.get_current_defense(),
                    'current_score': game_state.score,
                    'batter': current_batter.get('player', {}).get('fullName'),
                    'pitcher': current_pitcher.get('player', {}).get('fullName'),
                    'result': play_result.to_dict(),
                    'scored_runners': play_result.scored_runners,  
                    'pitch_details': play_result.pitch_details,
                    'pitch_count': play_result.pitch_count
                }
                
                stats_details = {
                    'batter_name': current_batter.get('player', {}).get('fullName'),
                    'pitcher_name': current_pitcher.get('player', {}).get('fullName'),
                    'batter_id': current_batter.id,
                    'pitcher_id': current_pitcher.id,
                    'batter_position': current_batter.position,
                    'position': 'P' if current_pitcher else current_batter.position,
                    'final_exit_velocity': play_result.final_exit_velocity,
                    'final_result': play_result.final_result,
                    'final_hit': play_result.final_hit,
                    'final_fielded_out': play_result.final_fielded_out,
                    'batting_team': game_state.batting_team.name,
                    'fielding_team': game_state.fielding_team.name,
                    'scored_runners': game_state._scored_runners_cache,  
                    'pitch_count': play_result.pitch_count,
                    'final_pitch_velocity': play_result.final_pitch_velocity,
                    'outs': game_state.outs,
                    'distance': getattr(play_result.final_distance, 'distance', 0),
                    'inning': game_state.inning
                }
                
                game_stats_manager.record_play(stats_details)
                
                play_result_str, final_outs = game_state.update(play_result)
                
                self.event_manager.emit('play_result', {
                    'play_details': play_details
                })

                sleep(7)
                
            game_summary, llm_analysis = game_stats_manager.generate_summary(
                final_score=game_state.score,
                innings_played=game_state.inning
            )
            
            self.event_manager.emit('game_status', {
            'message': 'Game Over',
            'type': 'end',
            'final_score': game_state.score,
            'innings': game_state.inning,
            'game_summary': game_summary.to_dict(),
            'llm_analysis': llm_analysis
        })

            play_details.update({
                'final_score': game_state.final_score,
                'innings': game_state.inning,
                'game_summary': game_summary.to_dict(),
                'llm_analysis': llm_analysis
            })
                    
            return play_details, stats_details
        
        except Exception as e:
            raise ValueError(f"Error simulating matchup: {str(e)}")