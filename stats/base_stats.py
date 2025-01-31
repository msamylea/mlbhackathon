from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging
from constants import PITCH_CODES

logger = logging.getLogger(__name__)

def safe_convert_to_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float"""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            value = value.replace('-.-', '0.0')
            value = value.strip('-')
            return float(value) if value else default
        except ValueError:
            return default
    return default

def safe_convert_to_int(value: Any, default: int = 0) -> int:
    """Safely convert any value to int"""
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default

@dataclass
class BattingStats:
    year: int = 2024
    games_played: int = 0
    avg: float = 0.250
    obp: float = 0.320
    slg: float = 0.400
    ops: float = 0.720
    babip: float = 0.300
    woba: float = 0.320
    wrc_plus: int = 100
    iso: float = 0.150
    
    at_bats: int = 0
    sac_flies: int = 0
    plate_appearances: int = 0
    hits : int = 0
    walks: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    strikeouts: int = 0
    strikeouts_per_pa: float = 0.214  
    walks_per_pa: float = 0.061
    groundouts: int = 0
    flyouts: int = 0
    airouts: int = 0
    popouts: int = 0
    base_on_balls: int = 0
    bat_hand: str = 'R'
    
    launch_speed: Dict = field(default_factory=lambda: {'avg': 85.0, 'min': 75.0, 'max': 95.0})
    launch_angle: Dict = field(default_factory=lambda: {'avg': 12.0, 'min': 0.0, 'max': 25.0})
    distance: Dict = field(default_factory=lambda: {'avg': 300.0, 'min': 250.0, 'max': 350.0})
    effective_speed: Dict = field(default_factory=lambda: {'avg': 90.0, 'min': 85.0, 'max': 95.0})
    
    
    @property
    def fielded_outs(self) -> int:
        return self.groundouts + self.flyouts + self.airouts + self.popouts
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method"""
        return getattr(self, key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style item access"""
        return getattr(self, key)
    
    def to_dict(self) -> Dict:
        """Convert stats to dictionary format"""
        return {
            'year': self.year,
            'games_played': self.games_played,
            'avg': self.avg,
            'obp': self.obp,
            'slg': self.slg,
            'ops': self.ops,
            'woba': self.woba,
            'wrc_plus': self.wrc_plus,
            'iso': self.iso,
            
            'at_bats': self.at_bats,
            'sac_flies': self.sac_flies,
            'plate_appearances': self.plate_appearances,
            'hits': self.hits,
            'walks': self.walks,
            'singles': self.singles,
            'doubles': self.doubles,
            'triples': self.triples,
            'home_runs': self.home_runs,
            'strikeouts': self.strikeouts,
            'strikeouts_per_pa': self.strikeouts_per_pa,
            'walks_per_pa': self.walks_per_pa,
            'base_on_balls': self.base_on_balls,
            'fielded_outs': self.fielded_outs,
            'groundouts': self.groundouts,
            'flyouts': self.flyouts,
            'airouts': self.airouts,
            'popouts': self.popouts,
            
            'babip': self.babip,
            'bat_hand': self.bat_hand,
           
            'launch_speed': self.launch_speed,
            'launch_angle': self.launch_angle,
            'distance': self.distance,
            'effective_speed': self.effective_speed
        }

    
                
    @classmethod
    def from_api_response(cls, data: Dict, year: int) -> 'BattingStats':
        stats_data = data.get('player', {}).get('stats', {})

        if not stats_data or not isinstance(stats_data, dict):
            logger.error("Invalid or missing stats data")
            return None  

            
        try:
            def convert_percentage(value: str, default: float) -> float:
                    """Convert string percentage to float, handling MLB API formats"""
                    if isinstance(value, str):
                        cleaned = value.strip()
                        if not cleaned:
                            return default
                        if cleaned.startswith('.'):
                            cleaned = '0' + cleaned
                        try:
                            return float(cleaned)
                        except ValueError:
                            return default
                    return safe_convert_to_float(value, default)
                
            return cls(
                bat_hand=stats_data.get('batSide', 'R'),
                year=year,
                games_played=int(safe_convert_to_int(stats_data.get('gamesPlayed', 0))),
                
                avg=convert_percentage(stats_data.get('avg', '.250'), 0.250),
                obp=convert_percentage(stats_data.get('obp', '.320'), 0.320),
                slg=convert_percentage(stats_data.get('slg', '.400'), 0.400),
                ops=convert_percentage(stats_data.get('ops', '.720'), 0.720),
                babip=convert_percentage(stats_data.get('babip', '.300'), 0.300),
                woba=convert_percentage(stats_data.get('woba', '.320'), 0.320),
                wrc_plus=int(safe_convert_to_int(stats_data.get('wrcPlus', 100))),
                iso=convert_percentage(stats_data.get('iso', '.150'), 0.150),
                
                at_bats=int(safe_convert_to_int(stats_data.get('atBats', 0))),
                sac_flies=int(safe_convert_to_int(stats_data.get('sacFlies', 0))),
                plate_appearances=int(safe_convert_to_int(stats_data.get('plateAppearances', 0))),
                hits=int(safe_convert_to_int(stats_data.get('hits', 0))),
                singles = safe_convert_to_int(stats_data.get('hits', 0)) - safe_convert_to_int(stats_data.get('doubles', 0)) - safe_convert_to_int(stats_data.get('triples', 0)) - safe_convert_to_int(stats_data.get('homeRuns', 0)),
                walks=int(safe_convert_to_int(stats_data.get('baseOnBalls', 0))),
                doubles=int(safe_convert_to_int(stats_data.get('doubles', 0))),
                triples=int(safe_convert_to_int(stats_data.get('triples', 0))),
                home_runs=int(safe_convert_to_int(stats_data.get('homeRuns', 0))),
                strikeouts=int(safe_convert_to_int(stats_data.get('strikeOuts', 0))),
                strikeouts_per_pa=safe_convert_to_float(stats_data.get('strikeoutsPerPlateAppearance', 0.000), 0.000),
                walks_per_pa=safe_convert_to_float(stats_data.get('walksPerPlateAppearance', 0.000), 0.000),
                base_on_balls=int(safe_convert_to_int(stats_data.get('baseOnBalls', 0))),
                groundouts=int(safe_convert_to_int(stats_data.get('groundOuts', 0))),
                flyouts=int(safe_convert_to_int(stats_data.get('flyOuts', 0))),
                airouts=int(safe_convert_to_int(stats_data.get('airOuts', 0))),
                popouts=int(safe_convert_to_int(stats_data.get('popOuts', 0))),
                                           
                launch_speed=stats_data.get('launch_speed', {
                    'avg': 85.0,
                    'min': 75.0,
                    'max': 95.0
                }),
                launch_angle=stats_data.get('launchangle', {
                    'avg': 12.0,
                    'min': 0.0,
                    'max': 25.0
                }),
                distance=stats_data.get('distance', {
                    'avg': 300.0,
                    'min': 250.0,
                    'max': 350.0
                }),
                effective_speed=stats_data.get('effectivespeed', {
                    'avg': 90.0,
                    'min': 85.0,
                    'max': 95.0
                })
            )
        except Exception as e:
            logger.error(f"Error creating stats: {e}")
            return None
    
@dataclass
class PitchingStats():
    """Enhanced pitching statistics"""
    year: int = 2024
    games_played: int = 0
    
    era: float = 4.50
    whip: float = 1.30
    babip: float = 0.300
    xfip: float = 4.50
    pli: float = 1.30

    innings_pitched: float = 0.0
    at_bats: int = 0
    sac_flies: int = 0
    batters_faced: int = 0
    hits: int = 0
    walks: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    base_on_balls: int = 0
    strikeouts: int = 0
    k_per_pa: float = 4.01            
    bb_per_pa: float = .90
    k_per_9: float = 9.0
    bb_per_9: float = 2.0            
    groundouts: int = 0
    flyouts: int = 0
    airouts: int = 0
    popouts: int = 0
    pitch_hand: str = 'R'
    
    launch_speed: Dict = field(default_factory=lambda: {'avg': 85.0, 'min': 75.0, 'max': 95.0})
    launch_angle: Dict = field(default_factory=lambda: {'avg': 12.0, 'min': 0.0, 'max': 25.0})
    distance: Dict = field(default_factory=lambda: {'avg': 300.0, 'min': 250.0, 'max': 350.0})
    effective_speed: Dict = field(default_factory=lambda: {'avg': 90.0, 'min': 85.0, 'max': 95.0})
    release_speed: Dict = field(default_factory=lambda: {'avg': 92.0, 'min': 87.0, 'max': 97.0})

    @property
    def fielded_outs(self) -> int:
        """Calculate fielded outs from plate appearances and strikeouts"""
        return self.groundouts + self.flyouts + self.airouts + self.popouts
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method"""
        return getattr(self, key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Dictionary-style item access"""
        return getattr(self, key)
    
    def to_dict(self) -> Dict:
        """Convert stats to dictionary format"""
        return {
            'era': self.era,
            'whip': self.whip,
            'babip': self.babip,
            'xfip': self.xfip,
            'pli': self.pli,
            
            'innings_pitched': self.innings_pitched,
            'at_bats': self.at_bats,
            'sac_flies': self.sac_flies,
            'batters_faced': self.batters_faced,
            'hits': self.hits,
            'walks': self.walks,
            'singles': self.singles,
            'doubles': self.doubles,
            'triples': self.triples,
            'home_runs': self.home_runs,
            'base_on_balls': self.base_on_balls,
            'strikeouts': self.strikeouts,
            'k_per_pa': self.k_per_pa,
            'bb_per_pa': self.bb_per_pa,
            'k_per_9': self.k_per_9,
            'bb_per_9': self.bb_per_9,
            'fielded_outs': self.fielded_outs,

            'year': self.year,
            'games_played': self.games_played,
            'pitch_hand': self.pitch_hand,
            
            'launch_speed': self.launch_speed,
            'launch_angle': self.launch_angle,
            'distance': self.distance,
            'effective_speed': self.effective_speed,
            'release_speed': self.release_speed
            
        }
        
    @classmethod
    def from_api_response(cls, data: Dict, year: int) -> 'PitchingStats':
        """Create pitching stats from API response"""
        try:
            
            career_stats = data.get('player', {}).get('stats', {})
         
            def convert_percentage(value: str, default: float) -> float:
                if isinstance(value, str):
                    cleaned = value.strip()
                    if not cleaned:
                        return default
                    try:
                        return float(cleaned)
                    except ValueError:
                        return default
                return safe_convert_to_float(value, default)

            stats = cls(
                pitch_hand=career_stats.get('pitchSide', 'R'),
                year=year,
                games_played=safe_convert_to_int(career_stats.get('gamesPitched', 0)),
                
                era=convert_percentage(career_stats.get('era', '4.50'), 4.50),
                whip=convert_percentage(career_stats.get('whip', '1.30'), 1.30),
                babip=convert_percentage(career_stats.get('babip', '0.300'), 0.300),
                xfip=convert_percentage(career_stats.get('xfip', '4.50'), 4.50),
                pli=convert_percentage(career_stats.get('pli', '1.30'), 1.30),
                  
                innings_pitched=safe_convert_to_float(career_stats.get('inningsPitched', 0.0)),
                at_bats=safe_convert_to_int(career_stats.get('atBats', 0)),
                sac_flies=safe_convert_to_int(career_stats.get('sacFlies', 0)),
                singles = safe_convert_to_int(career_stats.get('hits', 0)) - safe_convert_to_int(career_stats.get('doubles', 0)) - safe_convert_to_int(career_stats.get('triples', 0)) - safe_convert_to_int(career_stats.get('homeRuns', 0)),
                batters_faced=safe_convert_to_int(career_stats.get('battersFaced', 0)),
                hits=safe_convert_to_int(career_stats.get('hits', 0)),
                walks=safe_convert_to_int(career_stats.get('baseOnBalls', 0)),
                doubles=safe_convert_to_int(career_stats.get('doubles', 0)),
                triples=safe_convert_to_int(career_stats.get('triples', 0)),
                home_runs=safe_convert_to_int(career_stats.get('homeRuns', 0)),
                base_on_balls=safe_convert_to_int(career_stats.get('baseOnBalls', 0)),
                strikeouts=safe_convert_to_int(career_stats.get('strikeOuts', 0)),
                k_per_pa=safe_convert_to_float(career_stats.get('strikeoutsPerPlateAppearance', 0.55), 0.55),
                bb_per_pa=safe_convert_to_float(career_stats.get('walksPerPlateAppearance', 0.60), 0.60),
                k_per_9=safe_convert_to_float(career_stats.get('strikeoutsPer9Inn', 9.0), 9.0),
                bb_per_9=safe_convert_to_float(career_stats.get('walksPer9Inn', 2.0), 2.0),
                groundouts=safe_convert_to_int(career_stats.get('groundOuts', 0)),
                flyouts=safe_convert_to_int(career_stats.get('flyOuts', 0)),
                airouts=safe_convert_to_int(career_stats.get('airOuts', 0)),
                popouts=safe_convert_to_int(career_stats.get('popOuts', 0)),
                             
                launch_speed=data.get('player', {}).get('stats', {}).get('launch_speed', {
                    'avg': 85.0,
                    'min': 75.0,
                    'max': 95.0
                }),
                launch_angle=data.get('player', {}).get('stats', {}).get('launchangle', {
                    'avg': 12.0,
                    'min': 0.0,
                    'max': 25.0
                }),
                distance=data.get('player', {}).get('stats', {}).get('distance', {
                    'avg': 300.0,
                    'min': 250.0,
                    'max': 350.0
                }),
                effective_speed=data.get('player', {}).get('stats', {}).get('effectivespeed', {
                    'avg': 90.0,
                    'min': 85.0,
                    'max': 95.0
                }),
                release_speed=data.get('player', {}).get('stats', {}).get('releasespeed', {
                    'avg': 92.0,
                    'min': 87.0,
                    'max': 97.0
                })
            )
            return stats
        
        except Exception as e:
            return cls(year=year)

                
@dataclass
class Pitch:
    """Individual pitch type information"""
    _code: str
    _name: str
    _percentage: float = 0.0
    _avg_speed: float = 0.0
    
    def __init__(self, code: str, name: str, percentage: float = 0.0, avg_speed: float = 0.0):
        self._code = code
        self._name = name 
        self._percentage = percentage
        self._avg_speed = avg_speed
        
    @property
    def code(self) -> str:
        return self._code
    
    @property
    def name(self) -> str:
        return self._name
    
    @property 
    def percentage(self) -> float:
        return self._percentage
    
    @property
    def avg_speed(self) -> float:
        return self._avg_speed
        
@dataclass
class PitchArsenal:
    """Represents a pitcher's full pitch arsenal"""
    pitches: Dict[str, Pitch] = field(default_factory=dict)
    primary_pitch: Optional[str] = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-style get method"""
        return getattr(self, key, default)

    def add_pitch(self, code: str, percentage: float = 0.0, speed: float = 0.0) -> None:
        """Add a pitch to the arsenal"""
        name = PITCH_CODES.get(code, 'Unknown Pitch')
        self.pitches[code] = Pitch(
            code=code,
            name=name,
            percentage=percentage,
            avg_speed=speed
        )
        
        if not self.primary_pitch or percentage > self.pitches[self.primary_pitch].percentage:
            self.primary_pitch = code

    @classmethod
    def get_default_arsenal(cls) -> Dict:
        """Create default pitch arsenal dictionary"""
        return {
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
                },
                'CH': {
                    'code': 'CH',
                    'name': 'Changeup',
                    'percentage': 15.0,
                    'avg_speed': 83.0
                },
                'CU': {
                    'code': 'CU',
                    'name': 'Curveball',
                    'percentage': 15.0,
                    'avg_speed': 78.0
                }
            },
            'primary_pitch': 'FF'
        }
    
    @classmethod
    def from_api_response(cls, data: Dict) -> Dict:
        """Create pitch arsenal from API response"""
        arsenal = cls()
        try:
            people = data.get('people', [])
            if not people:
                return cls.get_default_arsenal()
                
            person = people[0]
            stats = person.get('stats', [])
            
            pitch_stats = next(
                (stat for stat in stats if stat.get('type', {}).get('displayName') == 'pitchArsenal'),
                None
            )
            if not pitch_stats:
                return cls.get_default_arsenal()

            splits = pitch_stats.get('splits', [])
            if not splits:
                return cls.get_default_arsenal()
                
            result = {
                'pitches': {},
                'primary_pitch': None
            }
            
            max_percentage = 0
            
            for split in splits:
                stat = split.get('stat', {})
                pitch_type = stat.get('type', {})
                
                if pitch_type:
                    code = pitch_type.get('code', '')
                    percentage = float(stat.get('percentage', 0)) * 100
                    speed = float(stat.get('averageSpeed', 0))
                    
                    result['pitches'][code] = {
                        'code': code,
                        'name': PITCH_CODES.get(code, 'Unknown Pitch'),
                        'percentage': percentage,
                        'avg_speed': speed
                    }
                    
                    if percentage > max_percentage:
                        max_percentage = percentage
                        result['primary_pitch'] = code

            return result if result['pitches'] else cls.get_default_arsenal()

        except Exception as e:
            return cls.get_default_arsenal()