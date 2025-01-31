
import random

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
        elif hasattr(pitch_type, 'value'):  
            pitch_type_str = str(pitch_type.value)
        else:  
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