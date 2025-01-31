import random
import json
import re
import json_repair
import traceback
from typing import Dict, List, Set
from constants import STRIKEOUT_TERMS, MAX_STRIKES, MAX_BALLS, VALID_RESULTS, HIT_TERMS, FIELDED_OUT_TERMS, RAW_PITCH_CODES, DEFAULT_PITCH_VELOCITY, map_action

def create_default_pitch_sequence(pitch_count: int) -> Dict:
    """Create a default pitch sequence for an at-bat"""
    try:
        strikes = 0
        balls = 0
        pitch_details = {}
        
        for i in range(pitch_count):
            pitch_type = random.choice(list(RAW_PITCH_CODES))
            
            if strikes < MAX_STRIKES  and balls < MAX_BALLS:
                hit_type = random.choice(['strike', 'ball'])
                if hit_type == 'strike':
                    strikes += 1
                else:
                    balls += 1
            elif strikes == 2:
                hit_type = 'strike'
                strikes += 1
            else:
                hit_type = 'ball'
                balls += 1
                
            pitch_details[f'pitch{i+1}'] = {
                'pitch_type': pitch_type,
                'hit_type': hit_type,
                'pitch_velocity': DEFAULT_PITCH_VELOCITY,
            }
        
        return {
            'pitch_count': pitch_count,
            'details': pitch_details
        }
    except Exception as e:
        raise ValueError(f"Error creating default pitch sequence: {str(e)}")
        
def extract_pitch_details(pitch_data: Dict) -> Dict:
    try:
        json_match = re.search(r'```json\s*({.*?})\s*```', pitch_data, re.DOTALL)
        if not json_match:
            return create_default_pitch_sequence(3)
        
        pitch_data = json_repair.loads(json_match.group(1).replace('null', '""').replace('[{', '{').replace('}]', '}').replace('[', '{').replace(']', '}').replace('[', '{').replace(']', '}'))
        
        if not pitch_data:
            return create_default_pitch_sequence(3)
        
        try:
            pitches = pitch_data.get('pitches', {})
            if isinstance(pitches, list):
                pitches = pitches[0].replace('[{', '{').replace('}]', '}').replace('[', '{').replace(']', '}')
                pitches_dict = json_repair.loads(pitches)
                
            else:
                pitches_dict = pitches
        except Exception:
            return create_default_pitch_sequence(3)
        
        if not pitches_dict:
            return create_default_pitch_sequence(3)
            
        return process_pitch_sequence(pitches_dict)
        
    except Exception:
        return create_default_pitch_sequence(3)

def parse_json_data(json_str: str) -> Dict:
    cleaned = json_str.replace('null', '""').replace('[{', '{').replace('}]', '}').replace('[', '{').replace(']', '}')
    return json_repair.loads(cleaned)

def get_pitches_dict(pitch_data: Dict) -> Dict:
    pitches = pitch_data.get('pitches', {})
    if isinstance(pitches, list):
        pitches = pitches[0].replace('[{', '{').replace('}]', '}').replace('[', '{').replace(']', '}')
        return json_repair.loads(pitches)
    return pitches

def process_pitch_sequence(pitches_dict: Dict) -> Dict:
    if not pitches_dict:
        return create_default_pitch_sequence(3)
        
    try:
        sorted_keys = sorted(pitches_dict.keys(), 
        key=lambda x: float(x.replace('pitch', '')) if x.replace('pitch', '').isdigit() else float('inf'))
    except ValueError:
        sorted_keys = list(pitches_dict.keys())
        
    pitches_to_delete = track_pitch_counts(pitches_dict, sorted_keys)
    
    final_dict = {k: pitches_dict[k] for k in sorted_keys if k not in pitches_to_delete}
    
    pitch_details = {
        pitch_key: {
            'hit_type': final_dict[pitch_key]['play_result'].lower(),
            'pitch_type': final_dict[pitch_key].get('pitch_type', ''),
        }
        for pitch_key in final_dict
    }
    
    return {'pitch_count': len(final_dict), 'details': pitch_details} if pitch_details else create_default_pitch_sequence(3)

def sort_pitch_keys(pitches_dict: Dict) -> List:
    try:
        return sorted(pitches_dict.keys(), 
                     key=lambda x: float(x.replace('pitch', '')) if x.replace('pitch', '').isdigit() else float('inf'))
    except ValueError:
        return list(pitches_dict.keys())

def track_pitch_counts(pitches_dict: Dict, sorted_keys: List) -> Set:
    strikes = balls = 0
    pitches_to_delete = set()
    
    for pitch_key in sorted_keys:
        pitch = pitches_dict[pitch_key]
        play_result = pitch.get('play_result', '').lower()
        
        if not play_result:
            return create_default_pitch_sequence(3)
            
        if any(result in play_result for result in ['foul', 'hit', 'ground out', 'grounds out', 
            'fly out', 'flies out', 'line out', 'lines out', 'bunt']):
            pitches_to_delete.add(pitch_key)
            continue
            
        if any(term in play_result for term in STRIKEOUT_TERMS):
            pitch['play_result'] = 'strike'
            strikes += 1
            if strikes >= MAX_STRIKES:
                pitches_to_delete.add(pitch_key)
            continue
            
        if 'strike' in play_result:
            strikes += 1
            if strikes >= MAX_STRIKES:
                pitches_to_delete.add(pitch_key)
                
        if 'ball' in play_result:
            balls += 1
            if balls >= MAX_BALLS:
                pitches_to_delete.add(pitch_key)
                
    return pitches_to_delete
                    
def extract_final_pitch_details(json_str: Dict) -> Dict:
    try:
        final_play = parse_json_input(json_str)
        return process_play_details(final_play)
    except Exception:
        return generate_fallback_result()

def parse_json_input(json_str):
    if isinstance(json_str, dict):
        return json_str.get('final_play', {})
    
    if isinstance(json_str, list):
        return next((item.get('final_play', {}) 
            for item in json_str 
            if isinstance(item, dict) and 'final_play' in item), {})
    
    if isinstance(json_str, str):
        cleaned = clean_json_string(json_str)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            data = json_repair.loads(cleaned)
        return parse_json_input(data)
    
    return {}

def clean_json_string(json_str: str) -> str:
    cleaned = (json_str
        .replace('null', '""')
        .replace('[{', '{')
        .replace('}]', '}')
        .replace('[', '{')
        .replace(']', '}'))
    return re.sub(r'(\w+)(?=\s*:)', r'"\1"', cleaned)

def process_play_details(final_play: Dict) -> Dict:
    result = {
        'final_pitch': str(final_play.get('final_pitch', 'FF')),
        'final_result': str(final_play.get('final_result', '')),
        'final_rationale': str(final_play.get('final_rationale', '')),
        'final_fielded_out': map_action(str(final_play.get('final_fielded_out', ''))),
        'final_hit': map_action(str(final_play.get('final_hit', '')))
    }
    
    return standardize_result(result)

def standardize_result(result: Dict) -> Dict:

    if result.get("final_fielded_out") in FIELDED_OUT_TERMS:
        result["final_result"] = "fielded out"
        result["final_hit"] = ""


    if result.get("final_hit") in HIT_TERMS:
        result["final_result"] = "hit"
        result["final_fielded_out"] = ""

    if result.get("final_result") in STRIKEOUT_TERMS:
        result["final_result"] = "strikeout"
        result["final_hit"] = ""
        result["final_fielded_out"] = ""

    if result.get("final_result") == "walk":
        result["final_hit"] = ""
        result["final_fielded_out"] = ""

    if result.get("final_result") == "fielded out":
        if result.get("final_fielded_out") not in FIELDED_OUT_TERMS:
            result["final_fielded_out"] = "grounds out"

        result["final_hit"] = ""

    if result.get("final_result") == "hit":
        if result.get("final_hit") not in HIT_TERMS:
            result["final_hit"] = "singles"

        result["final_fielded_out"] = ""

    if result.get("final_result") not in VALID_RESULTS:
        result.update({
            "final_result": "hit",
            "final_hit": "singles",
            "final_rationale": "The batter hits a single."
        })

    return result

def generate_fallback_result() -> Dict:
    outcomes = ['hit', 'fielded out', 'strikeout', 'walk']
    weights = [0.25, 0.45, 0.23, 0.07]
    final_result = random.choices(outcomes, weights=weights)[0]
    
    result = {
        'final_pitch': 'FF',
        'final_result': final_result,
        'final_hit': '',
        'final_fielded_out': '',
        'final_rationale': 'Result based on MLB averages'
    }
    
    if final_result == 'hit':
        result['final_hit'] = random.choice(['singles', 'doubles', 'triples', 'hits a home run'])
    elif final_result == 'fielded out':
        result['final_fielded_out'] = random.choice(['grounds out', 'flys out', 'lines out'])
    
    return result