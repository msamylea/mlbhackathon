from typing import Dict
from functools import lru_cache
from data.mlb_client import MLBDataClient
from stats.centralized_stats import CentralizedStatsService


class TeamDataLoader:
    """Handles all raw data loading from MLB API"""
    
    def __init__(self):
        self.mlb_client = MLBDataClient()
        self.stats_processor = CentralizedStatsService()
        
    def get_team_details(self, team_id: int, year: int) -> Dict:
        """Get raw team metadata"""
        try:
            return self.mlb_client.get_team_details(team_id, year)
        except Exception as e:
            return {}
            
    @lru_cache(maxsize=128)
    def get_player_stats(self, player_id: int, year: int) -> Dict:
        """Get raw player statistics"""
        try:
            return self.mlb_client.get_stats(player_id, year)
        except Exception as e:
            return {}

    @lru_cache(maxsize=128)
    def get_venue_data(self, team_id: int, year: int) -> Dict:
        """Get raw venue data"""
        try:
            return self.mlb_client.get_venue_details(team_id, year)
        except Exception as e:
            return {}
        
    @lru_cache(maxsize=128)
    def get_pitchers(self, team_id: int, year: int) -> Dict:
        """Get raw pitcher data"""
        try:
            return self.mlb_client.get_pitchers(team_id, year)
        except Exception as e:
            return {}

    @lru_cache(maxsize=128)
    def get_pitch_arsenal(self, pitcher_id: int, year: int) -> Dict:
        """Get raw pitch arsenal data"""
        try:
            return self.mlb_client.get_pitch_arsenal(pitcher_id, year)
        except Exception as e:
            return {}

    @lru_cache(maxsize=128)
    def load_complete_team_data(self, team_id: int, year: int) -> Dict:
        """Load all raw team data in coordinated fashion"""
        try:
 
            team_data = self.mlb_client.get_roster_with_stats(team_id, year)
            processed_data = self.stats_processor.process_team_stats(team_data, year)
            return processed_data

        except Exception as e:
            return {}
