from data.data_loader import TeamDataLoader
from stats.centralized_stats import CentralizedStatsService
from manager.player_manager import Player
from manager.roster_manager import TeamRoster
from stats.base_stats import BattingStats, PitchingStats
from typing import Dict, List, Optional
from manager.batter_selection import LineupOptimizer
from constants import REQUIRED_POSITIONS
import traceback

class TeamCreationService:
    """Handles creation of Team/TeamRoster objects"""
    def __init__(self, data_loader: TeamDataLoader, stats_service: CentralizedStatsService):
        self.data_loader = data_loader
        self.stats_service = stats_service
        self.lineup_optimizer = LineupOptimizer()
        
    def create_team(self, team_id, team_data: Dict, year: int, name: str) -> TeamRoster:
        """Create a TeamRoster with Players"""
        # First create all Player objects
        lineup = team_data.get('players', [])
        player_objects = [self._create_player(player, year) for player in lineup]
        
        # Get optimized lineup using Player objects
        _batter_lineup = self.lineup_optimizer.optimize_lineup(player_objects)
        
        # Get defense using Player objects
        _defense = self.assign_defense(player_objects)
        
        # Get pitchers and starting pitcher
        pitchers = [p for p in player_objects if p.position == 'P']
        starting_pitcher = self._get_starting_pitcher(team_id, year, pitchers)

        return TeamRoster(
            id=team_id,
            name=name,
            year=year,
            _current_batter_index=0,    
            roster=player_objects,
            starting_pitcher=starting_pitcher,
            pitch_arsenal=self._get_pitch_arsenal(starting_pitcher, year),
            _batter_lineup=_batter_lineup,
            _defense=_defense,
        )
  
    def set_stats(self, player_data: Player, stat_type: str, stats: Dict) -> Player:
        """Set stats for player"""
        if stat_type == 'batting':
            player_data.batting_stats = BattingStats(**stats)
        elif stat_type == 'pitching':
            player_data.pitching_stats = PitchingStats(**stats)
        return player_data
            
    def assign_defense(self, players: List[Player]) -> List[Player]:
        """
        Assigns players to defensive positions, handling OF/LF/CF/RF correctly
        
        Args:
            players: List of Player objects
            
        Returns:
            List of Player objects assigned to defensive positions
        """
        defense = []
        available_players = players[:]
        outfield_positions = {'LF', 'CF', 'RF'}
        assigned_positions = set()  
        required_positions = set(REQUIRED_POSITIONS)
        
        for pos in required_positions:
            if pos not in outfield_positions:
                for player in available_players[:]:  
                    if player.position == pos and pos not in assigned_positions:
                        defense.append(player)
                        assigned_positions.add(pos)
                        available_players.remove(player)
                        break
        
        available_outfielders = [p for p in available_players 
                            if p.position in {'OF', 'LF', 'CF', 'RF'}]
        
        for pos in outfield_positions:
            if pos not in assigned_positions:
                specific_pos_player = next(
                    (p for p in available_outfielders 
                    if p.position == pos), 
                    None
                )
                
                if specific_pos_player and specific_pos_player in available_players:
                    defense.append(specific_pos_player)
                    assigned_positions.add(pos)
                    available_outfielders.remove(specific_pos_player)
                    available_players.remove(specific_pos_player)
                
                elif available_outfielders:
                    of_player = next(
                        (p for p in available_outfielders 
                        if p.position == 'OF'),
                        available_outfielders[0] if available_outfielders else None
                    )
                    
                    if of_player and of_player in available_players:
                        defense.append(of_player)
                        assigned_positions.add(pos)
                        available_outfielders.remove(of_player)
                        available_players.remove(of_player)
        
        remaining_positions = required_positions - assigned_positions
        for pos in remaining_positions:
            if available_players:
                player = available_players.pop(0)
                defense.append(player)
                assigned_positions.add(pos)
        
        return defense

    def _get_pitchers(self, year, lineup) -> Dict:
        """Process players into categories"""
        try:
            players = {'pitchers': [], 'position': []}
            
            
            for player_entry in lineup:
                if 'player' in player_entry:
                    player_info = player_entry['player']
                    player_position = player_info.get('position', 'Utility')
                    if player_position == 'P':
                        players['pitchers'].append(player_entry)
                    else:
                        players['position'].append(player_entry)

            pitchers = players['pitchers']
        except Exception as e:
            raise ValueError(f"Error processing pitchers: {str(e)}")
            
        return pitchers
    
    def _create_player(self, player_data: Dict, year: int) -> Player:
        """Create Player object from processed data"""
        try:
            if 'player' in player_data:
                player_info = player_data.get('player', {})
                player_id = player_info.get('id')
                player_name = player_info.get('fullName')
                player_position = player_info.get('position')
                
                if player_position == 'P':
                    pitching_stats = self.stats_service.process_player_stats(player_data, year)
                    batting_stats = None
                else:
                    batting_stats = self.stats_service.process_player_stats(player_data, year)
                    pitching_stats = None
                
                return Player(
                    id=player_id,
                    name=player_name,
                    position=player_position,
                    year=year,
                    batting_stats=batting_stats,
                    pitching_stats=pitching_stats
                )
            else:
                raise ValueError("Invalid player data format")
                
        except Exception as e:
            raise ValueError(f"Error creating player: {str(e)}")
        
    def _get_starting_pitcher(self, team_id: int, year: int, pitchers: List[Player]) -> Optional[Player]:
        """Get starting pitcher from processed data"""
        try:
            pitchers_data = self.data_loader.get_pitchers(team_id, year)
            
            if not pitchers_data:
                return pitchers[0] if pitchers else None

            return self.stats_service.process_starting_pitcher(pitchers_data, pitchers)

        except Exception as e:
            traceback.print_exc()
            return pitchers[0] if pitchers else None
        
    def _get_pitch_arsenal(self, starting_pitcher: Player, year) -> Dict:
        """Get pitch arsenal for starting pitcher"""
        starting_pitcher_id = starting_pitcher.id
        
        pitch_arsenal = self.data_loader.get_pitch_arsenal(starting_pitcher_id, year)
     
        return self.stats_service.process_pitch_arsenal(pitch_arsenal)

    def _get_default_pitcher(self, processed_stats: Dict) -> Optional[Dict]:
        """Get first available pitcher from stats"""
        for player_data in processed_stats.values():
            if player_data['position'] == 'P':
                return player_data['player']
        return None
    
    def _create_default_arsenal(self) -> Dict:
        """Create default pitch arsenal when none is available"""
        return {
            'pitches': {
                'FF': {
                    'code': 'FF',
                    'name': 'Four-Seam Fastball',
                    'percentage': 50.0,
                    'avg_speed': 92.0
                },
                'SL': {
                    'code': 'SL', 
                    'name': 'Slider',
                    'percentage': 25.0,
                    'avg_speed': 84.0
                },
                'CH': {
                    'code': 'CH',
                    'name': 'Changeup',
                    'percentage': 25.0,
                    'avg_speed': 83.0
                }
            },
            'primary_pitch': 'FF'
        }
        
        
    def _create_default_position_player(self, index: int, year: int) -> Dict:
        """Create default position player with stats"""
        stats = self.stats_service._create_default_stats_dict('hitting')
        return {
            'player': {
                'id': -(index + 1),
                'fullName': f'Position Player {abs(index + 1)}',
                'position': 'Utility',
                'stats': stats
            },
           
        }