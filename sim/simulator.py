from typing import Dict, Union
from sim.game_state import GameState
from manager.batting_results import AtBatResult
from stats.centralized_stats import CentralizedStatsService
from constants import MAX_PITCHES, MAX_STRIKES, MAX_BALLS, DEFAULT_PITCH_VELOCITY, DEFAULT_PITCH_TYPE
from sim_utils.data_parsing import extract_final_pitch_details, extract_pitch_details
from prompts.play_prompt import create_pitch_prompt
from manager.pitch_manager import PitchSequenceManager, PitchResult
from manager.player_manager import Player
from calculations.gameplay_calcs import estimate_exit_velocity, estimate_pitch_velocity
from calculations.hit_distance_calc import calculate_hit
from sim_utils.historical_norms import get_league_rates


class EnhancedGameSimulator:
  
    def __init__(self, stats_service: CentralizedStatsService):
        self.stats_service = stats_service
        
                       
    def _get_stats_dict(self, stats) -> Dict:
        """Helper to convert stats object to dictionary"""
        if hasattr(stats, 'to_dict'):
            return stats.to_dict()
        if isinstance(stats, dict):
            return stats
        return {}

    def _get_player_name(self, player: Union[Player, Dict]) -> str:
        """Get player name with validation"""
        if isinstance(player, Player):
            return player.name
        player_data = player.get('player', {})
        return player_data.get('fullName', '')
        
    def _get_player_id(self, player: Union[Player, Dict]) -> int:
        """Get player ID with validation"""
        if isinstance(player, Player):
            return player.id
        player_data = player.get('player', {})
        return player_data.get('id', 0)   

    def confirm_pitch_sequence(self, sequence_manager: PitchSequenceManager, final_result: str) -> None:

        current_sequence = sequence_manager.sequence
        if not current_sequence:
            sequence_manager.add_pitch(PitchResult(
                pitch_type='FF',
                hit_type='strike' if final_result == 'strikeout' else 'ball' if final_result == 'walk' else final_result,
                pitch_velocity=93.0,
            ))
        current_sequence = sequence_manager.sequence
        
        if len(current_sequence) >MAX_PITCHES:
            sequence_manager.sequence = current_sequence[:MAX_PITCHES]
        
        strikes = sum(1 for pitch in current_sequence if 'strike' in pitch.hit_type.lower())
        balls = sum(1 for pitch in current_sequence if 'ball' in pitch.hit_type.lower())

        
        if final_result == 'strikeout' and strikes < MAX_STRIKES:
            needed_strikes = MAX_STRIKES - strikes
            for _ in range(needed_strikes):
                sequence_manager.add_pitch(PitchResult(
                    pitch_type=DEFAULT_PITCH_TYPE,
                    hit_type='strike',
                    pitch_velocity=DEFAULT_PITCH_VELOCITY,
                ))

        elif final_result == 'walk' and balls < MAX_BALLS:
            needed_balls = MAX_BALLS - balls
            for _ in range(needed_balls):
                sequence_manager.add_pitch(PitchResult(
                    pitch_type=DEFAULT_PITCH_TYPE,
                    hit_type='ball',
                    pitch_velocity=DEFAULT_PITCH_VELOCITY,
                ))
        
              
    def _build_context(self, game_state: GameState, batter_name: str, pitcher_name: str, 
                                            pitch_arsenal: Dict, normalized_batter, normalized_pitcher, home_year, bases) -> Dict:
        """Build context dictionary for simulation"""
        return {
            'batter': batter_name,
            'pitcher': pitcher_name,
            'outs': game_state.outs,
            'inning': game_state.inning,
            'score': game_state.current_score,
            'batting_team': game_state.batting_team.name,
            'fielding_team': game_state.fielding_team.name,            
            'venue': game_state.venue,           
            'arsenal': pitch_arsenal,
            'home_year': home_year,
            'normalized_batter': normalized_batter,
            'normalized_pitcher': normalized_pitcher,
            'bases': bases,
        }
        
    def simulate_at_bat(self, batter: Dict, pitcher: Dict, game_state: GameState, batter_stats, pitcher_stats, batter_year: int, pitcher_year: int) -> AtBatResult:
        try:
            batter_name = self._get_player_name(batter)
            pitcher_name = self._get_player_name(pitcher)
            batter_stats_dict = self._get_stats_dict(batter_stats)
            pitcher_stats_dict = self._get_stats_dict(pitcher_stats)
            home_year = game_state.home_year
            
            normalized_batter = get_league_rates(home_year, batter_stats, position='B')
            normalized_pitcher = get_league_rates(home_year, pitcher_stats, position='P')
      
            bases = game_state.bases
            context = self._build_context(
                game_state,
                batter_name,
                pitcher_name,
                game_state.pitch_arsenal,
                normalized_pitcher,
                normalized_batter,
                home_year,
                bases
            )
      
            try:
                at_bat_response = self.client.get_response(create_pitch_prompt(context))
            except Exception as e:
                raise e

            pitch_details = extract_pitch_details(at_bat_response)
            final_pitch_details = extract_final_pitch_details(at_bat_response)
            
            sequence_manager = PitchSequenceManager()
            pitch_count = pitch_details.get('pitch_count', 0)
            
            for i in range(1, pitch_count + 1):
                pitch_data = pitch_details['details'].get(f'pitch{i}')
                if not pitch_data:
                    continue

                pitch_velocity = estimate_pitch_velocity(
                    stats=pitcher_stats_dict,
                    last_pitch=pitch_data.get('pitch_type', 'FF')
                )


                pitch_result = PitchResult(
                    pitch_type=pitch_data.get('pitch_type', 'FF'),
                    hit_type=pitch_data.get('hit_type', ''),
                    pitch_velocity=pitch_velocity,
                )



                sequence_manager.add_pitch(pitch_result)

            
            final_pitch = (final_pitch_details or {}).get('final_pitch', '')
            final_pitch_velocity = (final_pitch_details or {}).get('velocity', 0)
            final_result = final_pitch_details.get('final_result', '')
            final_hit = final_pitch_details.get('final_hit', '')
            final_fielded_out = final_pitch_details.get('final_fielded_out', '')
            final_rationale = final_pitch_details.get('final_rationale', '')

            self.confirm_pitch_sequence(sequence_manager, final_result)
            
            final_pitch_velocity = estimate_pitch_velocity(
                stats=pitcher_stats_dict,
                last_pitch=final_pitch
            )
    
            final_exit_velocity = 0.0
            final_distance = 0.0
            final_location = ''
    
            if final_result == 'hit':
                final_exit_velocity = estimate_exit_velocity(batter_stats_dict, final_pitch_velocity)
                final_distance, final_location = calculate_hit(
                    batter_stats=batter_stats_dict,
                    pitcher_stats=pitcher_stats_dict,
                    exit_velocity=final_exit_velocity,
                    hit_type=final_hit,
                    venue=game_state.venue,
                    bat_side=batter_stats_dict.get('bat_hand', 'R'),
                    pitch_velocity=final_pitch_velocity
                )
    
            elif final_result == 'fielded out':
                final_exit_velocity = estimate_exit_velocity(batter_stats_dict, final_pitch_velocity)
                final_distance, final_location = calculate_hit(
                    batter_stats=batter_stats_dict,
                    pitcher_stats=pitcher_stats_dict,
                    exit_velocity=final_exit_velocity,
                    hit_type=final_fielded_out,
                    venue=game_state.venue,
                    bat_side=batter_stats_dict.get('bat_hand', 'R'),
                    pitch_velocity=final_pitch_velocity
                )

            result = AtBatResult(
                pitch_sequence=sequence_manager.get_pitch_codes(),
                pitch_details=sequence_manager.get_sequence_as_dicts(),  
                final_pitch=final_pitch,
                final_result=final_result,
                final_hit=final_hit,
                final_fielded_out=final_fielded_out,
                final_rationale=final_rationale,
                final_pitch_velocity=final_pitch_velocity,
                final_exit_velocity=final_exit_velocity,
                final_distance=final_distance,
                final_location=final_location,
                pitch_count=len(sequence_manager.sequence),
                batter_name=batter_name,
                pitcher_name=pitcher_name,
                batter_stats=batter_stats,
                pitcher_stats=pitcher_stats,
                scored_runners=game_state.scored_runners,
            )
            
            return result
        
        except Exception as e:
            return AtBatResult(
                final_result="error",
                final_hit="",
                final_fielded_out="",
                final_exit_velocity=0,
                final_pitch_velocity=0,
                pitch_sequence=[],
                scored_runners=[],
                pitch_details=[],
                pitch_count=0
            )
    
    def _create_default_result(self, batter, pitcher, game_state):
        return AtBatResult(
            pitch_sequence=[],
            pitch_details=[],
            final_pitch="FF",
            final_result="strikeout",
            final_hit="",
            final_fielded_out="",
            final_rationale="Default result due to error",
            final_pitch_velocity=90.0,
            final_exit_velocity=0.0,
            final_distance=0.0,
            final_location="",
            pitch_count=3,
            batter_stats=None,
            pitcher_stats=None,
            scored_runners=[]
        )