from typing import Dict
from constants import RAW_PITCH_CODES

    
def create_pitch_prompt(context: Dict) -> str:
    batting_team_name = context.get("batting_team", "Batting Team")
    fielding_team_name = context.get("fielding_team", "Fielding Team")
    batter_name = context.get("batter", "Batter")
    pitcher_name = context.get("pitcher", "Pitcher")
    inning = context.get("inning", 1)
    outs = context.get("outs", 0)
    score = context.get("score", {})
    arsenal = context.get("arsenal", {})  
    normalized_batter_stats = context.get("normalized_batter", {})
    normalized_pitcher_stats = context.get("normalized_pitcher", {})
    home_year = context.get("home_year", 2021)
    bases = context.get("bases", [])
    
    
   
    if not arsenal or not isinstance(arsenal, dict):
        arsenal = {
            'pitches': {
                'FF': {
                    'code': 'FF',
                    'name': 'Four-Seam Fastball',
                    'percentage': 50.0,
                    'avg_speed': 93.5
                },
                'SL': {
                    'code': 'SL', 
                    'name': 'Slider',
                    'percentage': 20.0,
                    'avg_speed': 85.0
                }
            },
            'primary_pitch': 'FF'
        }

    arsenal_desc = []
    for code, pitch in arsenal.get('pitches', {}).items():
        arsenal_desc.append(f"{pitch['name']} ({pitch['percentage']:.1f}%, {pitch['avg_speed']:.1f} mph)")
    
    arsenal_text = " | ".join(arsenal_desc)
    

    prompt = f"""Simulate the final result of an at-bat between {batter_name} of the {batting_team_name} and {pitcher_name} of the {fielding_team_name}.
    This game is taking place between teams of different eras, so stats for the player have been normalized for the year {home_year}.
    
    If normalized values are provided, use those instead of the raw stats.  Give heavy weighting to strong contact hitters / sluggers for successful at bat results.
    Do not assume the pitcher knows any of the batter's statistics or tendencies. Each player will play according to their own strengths and weaknesses.

    Game Situation:    
    Inning: {inning}
    Outs: {outs}
    Score: {score}
    Base Runners: {bases}

    Batter Stats: 
    Normalized Stats: {normalized_batter_stats}
    
    Pitcher Stats: 
    Normalized Stats: {normalized_pitcher_stats}
    
    - Pitch Arsenal: {arsenal_text}
   
    Rules for generating your response:

    - When considering a fielded out, sometimes choose a hit type instead. Not all hit balls are fielded out.
    - Your rationale should ONLY discuss the batter/pitcher matchup and game situation
    - Generate a logical pitch sequence that use the provided pitch arsenal, game situation, and choices the pitcher would make logically for the matchup.
    - Strikeouts require 2 strikes, walks require 3 balls
    - Return pitch codes only, not pitch names
    - Do not specify fielding positions or hit locations
    
    Use ONLY this JSON format for your reply:
    ```json
    {{
        "final_play":
        {{  
            "final_pitch": "One of {RAW_PITCH_CODES}",
            "final_result": "strikeout|walk|hit|fielded out",
            "final_hit": "singles|doubles|triples|hits a home run",
            "final_fielded_out": "grounds out|flys out|lines out",
            "final_rationale": "Statistical analysis of the overall play result"
        }},
        "pitches": 
        {{
            "pitch1": {{
                "play_result": "strike|ball",
                "pitch_type": "One of {RAW_PITCH_CODES}"
            }}
            Additional pitches following same format...
        }}
    }}
    ```"""

    return prompt