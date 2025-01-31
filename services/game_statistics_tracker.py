from typing import Dict, List, Optional, Tuple
from services.game_statistics_models import GameAtBatStats, GamePitchingStats

class PitchingStatsTracker:
    """Handles tracking and updating pitching statistics with comprehensive validation"""
    
    VALID_RESULTS = {'strikeout', 'walk', 'fielded out', 'hit'}
    VALID_HIT_TYPES = {'singles', 'doubles', 'triples', 'hits a home run'}
    
    @staticmethod
    def validate_pitch_velocity(velocity: float) -> bool:
        """Validate pitch velocity is within reasonable range (60-105 mph)"""
        return 60 <= velocity <= 105
        
    @staticmethod
    def validate_innings_pitched(innings: float) -> bool:
        """Validate innings pitched format (whole number or .1 or .2)"""
        decimal_part = innings % 1
        return decimal_part in (0.0, 0.1, 0.2)

    @staticmethod  
    def update_stats(stats: Optional[GamePitchingStats], stats_details: Dict) -> Tuple[GamePitchingStats, List[str]]:
        """Update pitching statistics with comprehensive validation"""
        if not stats:
            raise ValueError("Stats object must be initialized before updating")
            
        # Validate input data
        result = stats_details.get('final_result', '')
        if result and result not in PitchingStatsTracker.VALID_RESULTS:
            raise ValueError(f"Invalid result: {result}")
            
        pitch_velocity = stats_details.get('final_pitch_velocity')
        pitch_count = stats_details.get('pitch_count', 0)
        
        # Validate pitch count
        if pitch_count < 0:
            raise ValueError(f"Invalid pitch count: {pitch_count}")
        
        # Update pitch velocity stats with validation
        if pitch_velocity is not None:
            if not PitchingStatsTracker.validate_pitch_velocity(pitch_velocity):
                raise ValueError(f"Invalid pitch velocity: {pitch_velocity}")
            stats.pitch_velocity.append(pitch_velocity)
            
        # Update pitch count
        stats.pitches_thrown += pitch_count
            
        # Handle results with validation
        if result == 'strikeout':
            stats.total_strikeouts += 1
            stats.strikeouts += 1
        elif result == 'walk':
            stats.walks += 1
        elif result == 'fielded out':
            stats.fielded_out_hits += 1
            
        # Handle hits with validation
        hit_result = stats_details.get('final_hit', '')
        if hit_result and hit_result not in PitchingStatsTracker.VALID_HIT_TYPES:
            raise ValueError(f"Invalid hit type: {hit_result}")
            
        if hit_result in PitchingStatsTracker.VALID_HIT_TYPES:
            stats.hits_allowed += 1
            
        # Update earned runs with validation
        scored_runners = stats_details.get('scored_runners', [])
        if not isinstance(scored_runners, list):
            raise ValueError("scored_runners must be a list")
        stats.earned_runs += len(set(scored_runners))
            
        outs = stats_details.get('outs', 0)
        if not isinstance(outs, int) or outs < 0 or outs > 3:
            raise ValueError(f"Invalid number of outs: {outs}")
            
        if stats_details.get('inning') > stats.innings_pitched:
            stats.innings_pitched += 1
            
                   
      
        return stats
    
class BattingStatsTracker:
    """Handles tracking and updating batting statistics with enhanced validation"""
    
    VALID_RESULTS = {'walk', 'strikeout', 'hit', 'fielded out'}
    VALID_HIT_TYPES = {'singles', 'doubles', 'triples', 'hits a home run'}
    VALID_OUT_TYPES = {'grounds out', 'flies out', 'lines out'}

    @staticmethod
    def validate_exit_velocity(velocity: float) -> bool:
        """Validate exit velocity is within reasonable range (50-120 mph)"""
        return 50 <= velocity <= 120
    
    @staticmethod
    def update_stats(stats: Optional[GameAtBatStats], stats_details: Dict) -> Tuple[GameAtBatStats, List[str]]:
        """Update batting statistics with comprehensive validation"""
        if not stats:
            raise ValueError("Stats object must be initialized before updating")
        
        # Validate input data
        result = stats_details.get('final_result', '')
        if result and result not in BattingStatsTracker.VALID_RESULTS:
            raise ValueError(f"Invalid result: {result}")
            
        previous_hits = stats.hits  
        hit_increment = 0
         
        # Process result
        if result == 'walk':
            stats.walks += 1
        elif result == 'strikeout':
            stats.strikeouts += 1
            
        if result == 'hit':
            hit_type = stats_details.get('final_hit', '')
            if hit_type and hit_type not in BattingStatsTracker.VALID_HIT_TYPES:
                raise ValueError(f"Invalid hit type: {hit_type}")
            
        
            if hit_type == 'singles' or hit_type == 'single':
                hit_increment += 1
                stats.singles += 1
            elif hit_type == 'doubles' or hit_type == 'double':
                hit_increment += 1
                stats.doubles += 1
            elif hit_type == 'triples' or hit_type == 'triple':
                hit_increment += 1
                stats.triples += 1
            elif hit_type == 'hits a home run':
                hit_increment += 1
                stats.home_runs += 1

            stats.hits += hit_increment
            
            
        # Handle outs with validation
        if result == 'fielded out':
            out_type = stats_details.get('final_fielded_out', '')
            if out_type and out_type not in BattingStatsTracker.VALID_OUT_TYPES:
                raise ValueError(f"Invalid out type: {out_type}")
                
            if out_type == 'grounds out':
                stats.groundouts += 1
            elif out_type == 'flies out':
                stats.flyouts += 1
            elif out_type == 'lines out':
                stats.lineouts += 1
                
        if result == 'hit' or result == 'fielded out':
            exit_velocity = stats_details.get('final_exit_velocity')
            if exit_velocity is not None:
                if not BattingStatsTracker.validate_exit_velocity(exit_velocity):
                    raise ValueError(f"Invalid exit velocity: {exit_velocity}")
                stats.exit_velocity = exit_velocity
            
        # Update RBIs with validation
        scored_runners = stats_details.get('scored_runners', [])
        if scored_runners:
            if not isinstance(scored_runners, list):
                raise ValueError("scored_runners must be a list")
            unique_runners = list(set(scored_runners))
            stats.rbis += len(unique_runners)
            
        return stats