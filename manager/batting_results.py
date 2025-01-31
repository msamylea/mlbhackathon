from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

@dataclass
class AtBatResult:
    final_pitch: Optional[str] = None
    final_result: Optional[str] = None
    final_hit: Optional[str] = None
    final_fielded_out: Optional[str] = None
    final_rationale: Optional[str] = None
    final_pitch_velocity: Optional[int] = None
    final_exit_velocity: Optional[int] = None
    final_distance: Optional[int] = None
    final_location: Optional[str] = None
    pitch_sequence: List[str] = field(default_factory=list) 
    pitch_details: List[str] = field(default_factory=list)
    pitch_count: Optional[int] = None
    batter_name: Optional[str] = None
    pitcher_name: Optional[str] = None
    batter_stats: Optional[Dict] = None
    pitcher_stats: Optional[Dict] = None
    scored_runners: List[str] = field(default_factory=list)
    error: bool = False
    error_description: Optional[str] = None
    batter_df: Any = None
    pitcher_df: Any = None
        
    def _format_base_running(self) -> str:
        """Format base running results"""
        results = []
        if self.scored_runners:
            runners = ", ".join(self.scored_runners)
            results.append(f"{runners} scored")
        return ". ".join(results)
   

    def add_scored_runners(self, runners: List[str]) -> None:
        """Add scored runners to the result"""
        self.scored_runners.extend(runners)
        
    def to_dict(self) -> Dict:
        result = {
            'pitch_sequence': self.pitch_sequence,
            'pitch_details': [
                p if isinstance(p, dict) else p.to_dict() 
                for p in (self.pitch_details or [])
            ],
            'final_result': self.final_result,
            'final_hit': self.final_hit,
            'final_fielded_out': self.final_fielded_out,
            'final_rationale': self.final_rationale,
            'final_pitch': self.final_pitch,
            'final_pitch_velocity': self.final_pitch_velocity,
            'final_exit_velocity': self.final_exit_velocity,
            'final_distance': self.final_distance,
            'final_location': self.final_location,
            'pitch_count': self.pitch_count,
            'batter_name': self.batter_name,
            'pitcher_name': self.pitcher_name,
            'batter_stats': self.batter_stats,
            'pitcher_stats': self.pitcher_stats,
            'scored_runners': self.scored_runners,
            'error': self.error,
            'error_description': self.error_description,
            
        }
        
        if self.batter_df is not None:
            result['batter_df'] = self.batter_df.to_html(
                classes=['dataframe'],
                border=0,
                float_format=lambda x: '{:.3f}'.format(x) if isinstance(x, float) else x,
                justify='right',
                na_rep='-'
            )
            
        if self.pitcher_df is not None:
            result['pitcher_df'] = self.pitcher_df.to_html(
                classes=['dataframe'],
                border=0,
                float_format=lambda x: '{:.2f}'.format(x) if isinstance(x, float) else x,
                justify='right',
                na_rep='-'
            )
            
        return result
    

