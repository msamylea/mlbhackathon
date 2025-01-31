from typing import List, Dict, Tuple
from dataclasses import dataclass
from constants import PITCH_CODES

@dataclass
class PitchResult:
    pitch_type: str
    pitch_velocity: float
    hit_type: str
    
    def to_dict(self) -> Dict:
        """Convert PitchResult to a frontend-friendly format"""
        return {
            'pitch_type': self.pitch_type,
            'hit_type': self.hit_type,
            'pitch_velocity': self.pitch_velocity,
        }
        
    @classmethod
    def from_json(cls, data: Dict) -> 'PitchResult':
        """Create a PitchResult object from JSON data"""      
            
        return cls(
            pitch_type=data.get('pitch_type', 'FF'),
            pitch_velocity=data.get('pitch_velocity', 0.0),
            hit_type=data.get('play_result', ''),
        )

class PitchSequenceManager:
    """Manages a sequence of pitches in an at-bat"""
   
    def __init__(self):
        self.sequence: List[PitchResult] = []
        self.strikes = 0
        self.balls = 0
        self.pitch_count = 0
        
    def get_sequence_as_dicts(self) -> List[Dict]:
        """Convert sequence to list of dictionaries"""
        return [pitch.to_dict() for pitch in self.sequence]
    
    def add_pitch(self, pitch_result: PitchResult) -> None:
        """Add a pitch to the sequence and update count"""
        self.sequence.append(pitch_result)
        self.pitch_count += 1
        
        result = pitch_result.hit_type.lower()
        if 'ball' in result:
            self.balls += 1
        elif 'strike' in result or 'foul' in result:
            self.strikes += 1
                
    def get_pitch_codes(self) -> List[str]:
        """Get list of pitch type codes in sequence"""
        pitch_codes = [p.pitch_type for p in self.sequence]
        pitch_name = [PITCH_CODES.get(code, code) for code in pitch_codes]
        return pitch_name
        
    def get_balls_strikes(self) -> Tuple[int, int]:
        """Get the current count of balls and strikes"""
        return self.balls, self.strikes
