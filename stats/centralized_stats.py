from typing import Dict, Union, Tuple, List, Optional
import pandas as pd
from stats.base_stats import BattingStats, PitchingStats, PitchArsenal
from manager.player_manager import Player
from constants import DEFAULT_STATS, DEFAULT_ARSENAL, DEFAULT_METRICS
import logging
import warnings
import traceback

warnings.simplefilter(action='ignore', category=FutureWarning)
logger = logging.getLogger(__name__)

class CentralizedStatsService:
    """Handles all stats processing"""

    def process_stats_from_response(self, data: Dict, year: int):
        try:
            player_data = data.get('player', {})
            
            if not all([
                player_data,
                player_data.get('stats'),
                player_data.get('stat_type')
            ]):
                logger.error("Missing required player data fields")
                return None  
                
            # Extract stats based on type
            stats_type = player_data.get('stat_type')
            stats = player_data.get('stats')
            
            if stats_type == 'pitching':
                return PitchingStats.from_api_response(data, year)
            return BattingStats.from_api_response(data, year)
                
        except Exception as e:
            logger.error(f"Stats processing failed: {e}")
            return None
            
    def process_player_stats(self, processed_roster: Dict, year: int) -> Union[BattingStats, PitchingStats]:
        """Process raw player stats into stats object"""
        try:
            if not processed_roster:
                return self._create_default_stats(year)
            return self.process_stats_from_response(processed_roster, year)
        except Exception as e:
            logger.error(f"Error processing player stats: {e}")
            return self._create_default_stats(year)
    
    def process_metrics(self, stats_sections: List) -> Dict:
        """Process and aggregate metrics from multiple entries"""
        metrics_dict = DEFAULT_METRICS.copy()
        
        metrics = next((
            stat for stat in stats_sections
            if 'type' in stat and stat['type']['displayName'] == 'metricAverages'
        ), None)

        if metrics and 'splits' in metrics:
            metric_groups = {}
            for split in metrics['splits']:
                if 'stat' in split and 'metric' in split['stat']:
                    metric = split['stat']['metric']
                    metric_name = metric.get('name')
                    if metric_name in ['launchSpeed', 'launchAngle', 'distance', 'effectiveSpeed', 'releaseSpeed']:
                        if metric_name not in metric_groups:
                            metric_groups[metric_name] = {
                                'total_value': 0,
                                'total_occurrences': 0,
                                'min_value': float('inf'),
                                'max_value': float('-inf')
                            }
                        
                        occurrences = split.get('numOccurrences', 0)
                        if occurrences > 0:
                            value = metric.get('averageValue', 0)
                            min_val = metric.get('minValue', value)
                            max_val = metric.get('maxValue', value)
                            
                            group = metric_groups[metric_name]
                            group['total_value'] += value * occurrences
                            group['total_occurrences'] += occurrences
                            group['min_value'] = min(group['min_value'], min_val)
                            group['max_value'] = max(group['max_value'], max_val)

            for metric_name, group in metric_groups.items():
                key = metric_name.lower()
                if key == 'launchspeed':
                    key = 'launch_speed'
                    
                if group['total_occurrences'] > 0:
                    metrics_dict[key] = {
                        'avg': round(group['total_value'] / group['total_occurrences'], 1),
                        'min': round(group['min_value'], 1),
                        'max': round(group['max_value'], 1)
                    }
        
        return metrics_dict

    def _find_stat_section(self, stats_sections: List, section_type: str, group: str) -> Optional[Dict]:
        """Helper to find specific stat section"""
        return next((
            stat for stat in stats_sections
            if 'type' in stat 
            and stat['type'].get('displayName') == section_type
            and 'group' in stat 
            and stat['group'].get('displayName') == group
        ), None)
    
    def process_team_stats(self, raw_team_data: Dict, year: int) -> Dict:
        """Process raw team stats into processed stats"""
        try:
            processed_roster = {'players': []}

                
            for player in raw_team_data.get('roster'):
                try:
                    person = player.get('person', {})
                    player_id = person.get('id')
                    player_name = person.get('fullName')
                    position = person.get("primaryPosition", {}).get("abbreviation")
                    stat_type = 'pitching' if position == 'P' else 'hitting'
                    
                    bat_hand = 'R'
                    pitch_hand = 'R'
                    
                    if position != 'P':
                        bat_hand = person.get('batSide', {}).get('code', 'R')
                    else:
                        pitch_hand = person.get('pitchHand', {}).get('code', 'R')
                        
                    stats_sections = person.get('stats', {})
                 
                    career_stats = self._find_stat_section(stats_sections, 'career', stat_type)
                    advanced_stats = self._find_stat_section(stats_sections, 'careerAdvanced', stat_type)
                    sabermetrics = self._find_stat_section(stats_sections, 'sabermetrics', stat_type)
                    
                                        
                    basic_stats = career_stats['splits'][0].get('stat', {}) if career_stats and career_stats.get('splits') else {}
                    basic_stats['batSide'] = bat_hand
                    basic_stats['pitchSide'] = pitch_hand
                    advanced_stats = advanced_stats['splits'][0].get('stat', {}) if advanced_stats and advanced_stats.get('splits') else {}
                    sabermetrics = sabermetrics['splits'][0].get('stat', {}) if sabermetrics and sabermetrics.get('splits') else {}
                    
                    metrics_dict = self.process_metrics(stats_sections)
                        
                    if basic_stats:
                        combined_stats = {
                            **basic_stats,
                            **advanced_stats,
                            **sabermetrics,
                            **metrics_dict
                        }
                        
                        player_data = {
                            'player': {
                                'id': player_id,
                                'fullName': player_name,
                                'position': position,
                                'stat_type': stat_type,
                                'stats': combined_stats
                            }
                        }
                        
                    
                        
                        processed_roster['players'].append(player_data)
                        
                                       
                except Exception as e:
                    logger.error(f"Error processing player {player_name if 'player_name' in locals() else 'unknown'}: {e}")
                    continue

            return processed_roster

        except Exception as e:
            
            return {'players': []}
        
    def process_starting_pitcher(self, pitchers_data: Dict, pitchers: List[Player]) -> Player:
        """Process and select starting pitcher from roster"""
        if pitchers_data:
            for team_leader in pitchers_data.get('teamLeaders', []):
                for ranked_player in team_leader.get('leaders', []):
                    rank = ranked_player.get('rank', 0)
                    player_id = ranked_player['person']['id']
                    
                    if rank == 1:
                        for pitcher in pitchers:
                            if pitcher.id == player_id:
                                return pitcher
                                
        return pitchers[0] if pitchers else None
        
    def process_pitch_arsenal(self, raw_arsenal) -> PitchArsenal:
        """Process raw arsenal data into processed arsenal"""
        try: 
            arsenal = PitchArsenal.from_api_response(raw_arsenal)
            return arsenal
        except Exception as e:
            logger.error(f"Error processing pitch arsenal: {e}")
            return DEFAULT_ARSENAL

   
    def get_formatted_stat_tables(self, batter_stats, pitcher_stats):
        if not batter_stats or not pitcher_stats:
            return self._create_default_tables()
        try:
            def to_float(val, default=0.000):
                try:
                    return float(val)
                except (TypeError, ValueError):
                    return default
 
            if hasattr(batter_stats, 'to_dict'):
                batter_stats = batter_stats.to_dict()
            elif not isinstance(batter_stats, dict):
                batter_stats = {}
                
            if hasattr(pitcher_stats, 'to_dict'):
                pitcher_stats = pitcher_stats.to_dict()
            elif not isinstance(pitcher_stats, dict):
                pitcher_stats = {}

            # Create data frames
            batting_data = {
                'OBP': to_float(batter_stats.get('obp', '0.000')),
                'OPS': to_float(batter_stats.get('ops', '0.000')),
                'SLG': to_float(batter_stats.get('slg', '0.000')),
                'wOBA': to_float(batter_stats.get('woba', '0.000')),
                'K PER PA': to_float(batter_stats.get('strikeouts_per_pa', '0.000')),
                'BB PER PA': to_float(batter_stats.get('walks_per_pa', '0.000')),
                
            }

            pitching_data = {
                'ERA': to_float(pitcher_stats.get('era', 0.000)),
                'WHIP': to_float(pitcher_stats.get('whip', 0.000)),
                'BABIP': to_float(pitcher_stats.get('babip', 0.000)),
                'xFIP': to_float(pitcher_stats.get('xfip', 0.000)),
                'K PER PA': to_float(pitcher_stats.get('k_per_pa', 0.000)),
                'BB PER PA': to_float(pitcher_stats.get('bb_per_pa', 0.000)),
              
            }

            return self._format_stat_dataframes(batting_data, pitching_data)

        except Exception as e:
            logger.error(f"Error formatting stat tables: {e}")
            return self._create_default_tables()
    def _format_stat_dataframes(self, batting_data: Dict, 
                              pitching_data: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Format stat dictionaries into DataFrames"""
        batter_df = pd.DataFrame.from_dict(batting_data, orient='index', columns=[''])
        pitcher_df = pd.DataFrame.from_dict(pitching_data, orient='index', columns=[''])
        # Format values
        for idx in batter_df.index:
            value = batter_df.loc[idx, '']
            batter_df.loc[idx, ''] = f"{float(value):.3f}"
                
        for idx in pitcher_df.index:
            value = pitcher_df.loc[idx, '']
            if idx in ['ERA', 'WHIP', 'BABIP', 'xFIP','K PER PA', 'BB PER PA']:
                pitcher_df.loc[idx, ''] = f"{float(value):.3f}"
            else:
                pitcher_df.loc[idx, ''] = f"{int(value)}"
        return pitcher_df, batter_df  
        
    def _create_default_stats(self, year: int) -> Union[BattingStats, PitchingStats]:
        
        return BattingStats(year=year)
    
    def _create_default_stats_dict(self) -> Dict:
        """Create a default stats dictionary with realistic MLB averages"""
        
        return DEFAULT_STATS['hitting']

    def _create_default_tables(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Create default DataFrames for display using realistic MLB averages"""
        pitcher_data = {
            'ERA': '4.25',          
            'WHIP': '1.30',
            'BABIP': '0.300',
            'xFIP': '4.25',
            'K PER PA': '0.23',
            'BB PER PA': '0.08',
        }
        
        batter_data = {
            'OBP': '0.317',
            'SLG': '0.411',
            'OPS': '0.728',
            'wOBA': '0.320',      
            'BABIP': '0.300',
            'K PER PA': '0.23',
            'BB PER PA': '0.08',
            
        }
        
        return (
            pd.DataFrame.from_dict(pitcher_data, orient='index', columns=['']),
            pd.DataFrame.from_dict(batter_data, orient='index', columns=[''])
        )
