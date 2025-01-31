from calculations.venue_data import VenueData
from typing import Tuple, Union, Dict, Optional
from stats.base_stats import BattingStats, PitchingStats
import random

def determine_field_location() -> str:

    possible_locations = ['left line', 'left center', 'center', 'right center', 'right line']
    return random.choice(possible_locations)

def calculate_hit (
    batter_stats: Union[Dict, BattingStats], pitcher_stats: Union[Dict, PitchingStats], exit_velocity: float, hit_type: str, 
                             venue: Optional[VenueData] = None, bat_side: str = 'R',
                             pitch_velocity: float = 90.0) -> Tuple[float, str]:
    """
    Calculate a descriptive location (e.g., 'shallow left center') and distance
    based on angle, velocity, and venue. Returns (location_str, distance).
    """
    venue_data = venue or VenueData()
    
    launch_angle = pitcher_stats.get('launch_angle').get('avg', 12.0)
    
    final_location = determine_field_location()

    initial_distance = (exit_velocity * exit_velocity * 0.025) + (exit_velocity * 1.5)

    if launch_angle < 0: 
        initial_distance *= 0.4    # Severe ground ball
    elif launch_angle < 10: 
        initial_distance *= 0.7  # Low liner
    elif launch_angle < 20: 
        initial_distance *= 0.9  # Line drive
    elif launch_angle < 30: 
        initial_distance *= 1.05  # Optimal drive
    elif launch_angle < 40: 
        initial_distance *= 0.95 # High drive
    elif launch_angle < 50: 
        initial_distance *= 0.85 # High fly
    else: 
        initial_distance *= 0.7    
            
    if isinstance(batter_stats, dict):
        avg_distance = batter_stats.get('avg', 200.0)
       
    else:
        avg_distance = batter_stats.distance['avg']

    def calculate_elevation_factor(elev: int) -> float:
        return 1.0 + (venue.elevation / 5280) * 0.08 
    
    if venue.elevation is not None:
        elevation_factor = calculate_elevation_factor(venue.elevation)
        initial_distance = initial_distance * (1 + (elevation_factor - 1) * 0.7)

    velocity_factor = (exit_velocity - 85) * 1.5
    if exit_velocity > 100:
        velocity_factor *= 1.1 
        
    historical_factor = (avg_distance - 200) / 80 
    hit_distance = (initial_distance * (0.9 + (0.2 * historical_factor))) + velocity_factor
    
    if not venue_data:
        variation = min(hit_distance * 0.05, 15)  
        hit_distance += random.uniform(-variation, variation)
        
        
    if launch_angle < 10:
        def calculate_turf_factor(turf: str) -> float:
            factors = {"Artificial Turf": 1.1, "Grass": 1.0, "Dirt": 0.9}
            return factors.get(turf, 1.0)

        tf = calculate_turf_factor(venue.turf_type)
        adjusted_distance = min(hit_distance * tf, 150)
    else:
        adjusted_distance = min(hit_distance, 500)



    distance_by_position = {
        'pitcher': 55,
        'first base': 90,
        'second base': 140,
        'shortstop': 140,
        'third base': 90,
        'left field': 300,
        'center field': 400,
        'right field': 300
    }
    
    home_run_location = {
        'left line': "Left Field",
        'right line': "Right Field",
        'center': "Center Field",
        'left center': "Left Center Field",
        'right center': "Right Center Field"
    }
    
    home_run_min = {
        'left line': venue.left_line,
        'right line': venue.right_line,
        'center': venue.center,
        'left center': venue.left_center,
        'right center': venue.right_center
    }
    
    position_mapping = {
        'left line': ['third base', 'left field'],
        'left center': ['shortstop', 'left field'],
        'center': ['second base', 'center field', 'pitcher'],
        'right center': ['first base', 'right field'],
        'right line': ['first base', 'right field']
    }
    
    possible_positions = position_mapping[final_location]
    location_str = min(possible_positions, 
                      key=lambda x: abs(distance_by_position[x] - adjusted_distance))
      

    if hit_type == 'hits a home run':
        min_distance = home_run_min[final_location]
        adjusted_distance = random.randint(min_distance, min(min_distance + 75, 500))
        return adjusted_distance, home_run_location[final_location]
   
        
    return (round(adjusted_distance, 1), location_str)