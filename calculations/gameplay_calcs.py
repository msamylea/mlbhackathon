
from stats.base_stats import BattingStats
from stats.centralized_stats import CentralizedStatsService
from data.mlb_client import MLBDataClient
import random
from typing import Dict, Union

mlb_client = MLBDataClient()
stats_service = CentralizedStatsService()
        
def calculate_multiplier(pitch_velocity):
    if pitch_velocity < 80:
        multiplier = 1.35
    elif pitch_velocity < 90:
        multiplier = 1.40
    else:
        multiplier = 1.45
    return (pitch_velocity * multiplier) - 20

def estimate_exit_velocity(stats: Union[Dict, BattingStats], pitch_velocity: float) -> float:
    if not stats:
        return 0
    
    base_exit_velocity = calculate_multiplier(pitch_velocity)
    
    if isinstance(stats, dict):
        launch_speed = stats.get('launch_speed', {'avg': 88.0, 'min': 65.0, 'max': 115.0})
        avg_launch_speed = launch_speed.get('avg', 88.0)
        min_launch_speed = launch_speed.get('min', 65.0)
        max_launch_speed = launch_speed.get('max', 115.0)
    else:
        avg_launch_speed = stats.launch_speed['avg']
        min_launch_speed = stats.launch_speed['min']
        max_launch_speed = stats.launch_speed['max']
    
    historical_factor = (avg_launch_speed - 85) / 25  
    exit_velocity = base_exit_velocity * (0.85 + (0.3 * historical_factor)) 
    
    velocity_factor = (pitch_velocity - 90) * 0.3 
    exit_velocity += velocity_factor
    
    exit_velocity += random.uniform(-3.0, 3.0)
    
    exit_velocity = min(max(exit_velocity, min_launch_speed), max_launch_speed)
    
    return round(exit_velocity, 1)



def adjust_for_pitch_type(velocity: float, pitch_type) -> float:
    adjustments = {
        'FF': 1.5,   # Four-seam fastball
        'FT': 1.0,   # Two-seam fastball
        'FC': -2.0,  # Cutter
        'SL': -5.0,  # Slider
        'CH': -8.0,  # Changeup
        'CU': -8.0,  # Curveball
        'KC': -8.0,  # Knuckle-curve
        'SF': -4.0,  # Split-finger
        'EP': -20.0, # Eephus
        'KN': -20.0  # Knuckleball
    }
    
    if pitch_type:
        if hasattr(pitch_type, 'name'):  
            pitch_type_str = pitch_type.name
        elif hasattr(pitch_type, 'value'):  # 
            pitch_type_str = str(pitch_type.value)
        else:  # If it's already a string
            pitch_type_str = str(pitch_type)
            
        return velocity + adjustments.get(pitch_type_str, 0)

    return velocity 

def estimate_pitch_velocity(stats, last_pitch):
    avg_release_speed = stats.get('release_speed', {}).get('avg', 90.0)
    min_release_speed = stats.get('release_speed', {}).get('min', 80.0)
    max_release_speed = stats.get('release_speed', {}).get('max', 100.0)
    
    avg_effective_speed = stats.get('effective_speed', {}).get('avg', 88.0)
    min_effective_speed = stats.get('effective_speed', {}).get('min', 78.0)
    max_effective_speed = stats.get('effective_speed', {}).get('max', 98.0)

    pitch_velocity = avg_release_speed if avg_release_speed else avg_effective_speed
    
    pitch_velocity = adjust_for_pitch_type(pitch_velocity, last_pitch)
    
    velocity_difference = float(avg_effective_speed - pitch_velocity)
    pitch_velocity += velocity_difference * 0.1  
    
    if min_release_speed and max_release_speed:
        pitch_velocity = min(max(pitch_velocity, min_release_speed), max_release_speed)
    else:
        pitch_velocity = min(max(pitch_velocity, min_effective_speed), max_effective_speed)
    
    if avg_release_speed:
        historical_ratio = pitch_velocity / avg_release_speed
        pitch_velocity = avg_release_speed * max(0.9, min(1.1, historical_ratio))  
    
    pitch_velocity += random.uniform(-1.0, 1.0) 
    return round(pitch_velocity, 1)
