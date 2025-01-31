import re

MAX_STRIKES = 2  
MAX_BALLS = 3
MAX_PITCHES = 7
STRIKEOUT_TERMS = [
    'strikeout', 'strike out', 'struck out', 'struckout', 
    'strikedout', 'miss', 'swinging strike', 'swinging_strike',
    'strikeout looking', 'strikeout swinging', 'swinging strikeout'
]
FIELDED_OUT_TERMS = [
    'ground out', 'fly out', 'line out', 'grounds out', 
    'flies out', 'lines out', 'grounded out', 'flied out', 'lined out'
]
HIT_TERMS = [
    'single', 'double', 'triple', 'home run', 
    'singles', 'doubles', 'triples', 'home runs', 'hits a home run'
]
VALID_RESULTS = ['strikeout', 'walk', 'hit', 'fielded out']
DEFAULT_PITCH_VELOCITY = 93.0
DEFAULT_PITCH_TYPE = 'FF'
    
DEFAULT_ARSENAL = {
    'pitches': {
            'FF': {  # Four-seam fastball
                'code': 'FF',
                'name': 'Fastball',
                'percentage': 50.0,
                'avg_speed': 92.0
            },
            'SL': {  # Slider
                'code': 'SL',
                'name': 'Slider',
                'percentage': 25.0,
                'avg_speed': 84.0
            },
            'CH': {  # Changeup
                'code': 'CH',
                'name': 'Changeup',
                'percentage': 25.0,
                'avg_speed': 83.0
            },
            'primary_pitch': 'FF'
    }
}
            
    
DEFAULT_STATS = {
    'hitting': {
        'avg': 0.252,             # League average BA
        'obp': 0.317,             # League average OBP
        'slg': 0.411,             # League average SLG
        'ops': 0.728,             # League average OPS
        'woba': 0.320,            # League average wOBA
        'wrc_plus': 100,          # League average wRC+
        'iso': 0.159,             # League average ISO
        
        'plate_appearances': 600,  # Based on typical PA
        'strikeouts_per_pa': 0.23, # League average K rate
        'walks_per_pa': 0.08,      # League average BB rate
             
        'babip': 0.300,            # League average BABIP
        'bat_hand': 'R',           # Right-handed batter by default

        'games_played': 700,
                
        'launch_speed': {
            'avg': 88.0,   # MLB average is around 88-89 mph
            'min': 65.0,   # Weak contact/check swings
            'max': 115.0   # Hardest hit balls
        },
        'launch_angle': 
        {
            'avg': 12.0,    # Good average launch angle
            'min': -30.0,   # Ground balls can have negative angles
            'max': 45.0     # Pop ups can have high angles
        },
        'distance': 
        {
            'avg': 200.0,   # Average including all types of contact
            'min': 0.0,     # Includes bunts, weak grounders
            'max': 450.0    # Maximum realistic home run distance
        },
        'effective_speed': 
        {
            'avg': 92.0,     # Modern MLB average
            'min': 70.0,     # Slow breaking balls
            'max': 105.0     # Maximum effective velocity
        },
        'release_speed': 
        {
            'avg': 93.0,     # Modern MLB average
            'min': 75.0,     # Slow pitches (curves, changeups)
            'max': 102.0     # Maximum fastball velocity
        }
    },
        
    'pitching': {
        # Core Stats
        'era': 4.25,          # League average ERA
        'whip': 1.30,         # League average WHIP
        'babip': 0.300,       # League average BABIP
        'xfip': 4.25,         # League average xFIP
        'k_per_9': 8.5,       # League average K/9
        'bb_per_9': 3.0,      # League average BB/9
        
        # Rate Stats
        'k_per_pa': 0.23,     # League average K/PA
        'bb_per_pa': 0.08,    # League average BB/PA
               
        'hits': 150,          # League average hits allowed
                 
        'pitch_hand': 'R',      # Right-handed pitcher by default
        
        'year': 2024,
        'games_played': 700,
                
        'launch_speed': {
            'avg': 88.0,   # MLB average is around 88-89 mph
            'min': 65.0,   # Weak contact/check swings
            'max': 115.0   # Hardest hit balls
        },
        'launch_angle': 
        {
            'avg': 12.0,    # Good average launch angle
            'min': -30.0,   # Ground balls can have negative angles
            'max': 45.0     # Pop ups can have high angles
        },
        'distance': 
        {
            'avg': 200.0,   # Average including all types of contact
            'min': 0.0,     # Includes bunts, weak grounders
            'max': 450.0    # Maximum realistic home run distance
        },
        'effective_speed': 
        {
            'avg': 92.0,     # Modern MLB average
            'min': 70.0,     # Slow breaking balls
            'max': 105.0     # Maximum effective velocity
        },
        'release_speed': 
        {
            'avg': 93.0,     # Modern MLB average
            'min': 75.0,     # Slow pitches (curves, changeups)
            'max': 102.0     # Maximum fastball velocity
        }
    }
}

DEFAULT_METRICS = {
    'launch_speed': {  # Exit velocity
        'avg': 88.0,   # MLB average is around 88-89 mph
        'min': 65.0,   # Weak contact/check swings
        'max': 115.0   # Hardest hit balls
    },
    'launchangle': {
        'avg': 12.0,    # Good average launch angle
        'min': -30.0,   # Ground balls can have negative angles
        'max': 45.0     # Pop ups can have high angles
    },
    'distance': {
        'avg': 200.0,   # Average including all types of contact
        'min': 0.0,     # Includes bunts, weak grounders
        'max': 450.0    # Maximum realistic home run distance
    },
    'effectivespeed': {  # Perceived pitch speed
        'avg': 92.0,     # Modern MLB average
        'min': 70.0,     # Slow breaking balls
        'max': 105.0     # Maximum effective velocity
    },
    'releasespeed': {    # Actual pitch speed
        'avg': 93.0,     # Modern MLB average
        'min': 75.0,     # Slow pitches (curves, changeups)
        'max': 102.0     # Maximum fastball velocity
    }
}

team_mapping = {
	"108": "Los Angeles Angels",
	"109": "Arizona Diamondbacks",
	"110": "Baltimore Orioles",
	"111": "Boston Red Sox",
	"112": "Chicago Cubs",
	"113": "Cincinnati Reds",
	"114": "Cleveland Indians",
	"115": "Colorado Rockies",
	"116": "Detroit Tigers",
	"117": "Houston Astros",
	"118": "Kansas City Royals",
	"119": "Los Angeles Dodgers",
	"120": "Washington Nationals",
	"121": "New York Mets",
	"133": "Oakland Athletics",
	"134": "Pittsburgh Pirates",
	"135": "San Diego Padres",
	"136": "Seattle Mariners",
	"137": "San Francisco Giants",
	"138": "St. Louis Cardinals",
	"139": "Tampa Bay Rays",
	"140": "Texas Rangers",
	"141": "Toronto Blue Jays",
	"142": "Minnesota Twins",
	"143": "Philadelphia Phillies",
	"144": "Atlanta Braves",
	"145": "Chicago White Sox",
	"146": "Miami Marlins",
	"147": "New York Yankees",
	"158": "Milwaukee Brewers",
	"159": "AL All-Stars",
	"160": "NL All-Stars"
}

PITCH_CODES = {
    'FA': 'Fastball',
    'FF': 'Four-Seam Fastball',
    'FT': 'Two-Seam Fastball',
    'FC': 'Cutter',
    'FO': 'Forkball',
    'SI': 'Sinker',
    'SL': 'Slider',
    'ST': 'Sweeper',
    'CH': 'Changeup',
    'CU': 'Curveball',
    'KC': 'Knuckle-Curve',
    'KN': 'Knuckleball',
    'SF': 'Split-Finger',
    'SC': 'Screwball',
    'CS': 'Slow Curve',
    'FS': 'Splitter'
}

RAW_PITCH_CODES = {    
    'FA',
    'FF',
    'FT',
    'FC',
    'FO',
    'SI',
    'SL',
    'ST',
    'CH',
    'CU',
    'KC',
    'KN',
    'SF',
    'SC',
    'CS',
    'FS'
}

REQUIRED_POSITIONS = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']


ACTION_MAP =  {
    re.compile(r'.*\b(ground(ed|s)?|hits? a grounder)\b.*', re.IGNORECASE): 'grounds out',
    re.compile(r'.*\b(fly(ing|s)?|flies|flied|flew|pop(s|ped)?)\b.*', re.IGNORECASE): 'flies out',
    re.compile(r'.*\b(line(d|s)?|hits? a liner)\b.*', re.IGNORECASE): 'lines out',
    re.compile(r'.*\b(single[sd]?|hits? a single[sd]?)\b.*', re.IGNORECASE): 'singles',
    re.compile(r'.*\b(double[sd]?|hits? a double[sd]?)\b.*', re.IGNORECASE): 'doubles',
    re.compile(r'.*\b(triple[sd]?|hits? a triple[sd]?)\b.*', re.IGNORECASE): 'triples',
    re.compile(r'.*\b(home ?run[s]?|homer[s]?|hits? a home ?run)\b.*', re.IGNORECASE): 'hits a home run',
    re.compile(r'.*\b(walk[sed]?|base on balls|draws? a walk)\b.*', re.IGNORECASE): 'walks',
    re.compile(r'.*\b(strike(s)? ?out|struck out|whiff[sed]?|k\'s?)\b.*', re.IGNORECASE): 'strikeout',
}


LOCATION_MAP = {
    re.compile(r'.*\bshort stop(s)?\b.*', re.IGNORECASE): 'shortstop',
    re.compile(r'.*\bSS?\b.*', re.IGNORECASE): 'shortstop',
    re.compile(r'.*\b1B?\b.*', re.IGNORECASE): 'first base',
    re.compile(r'.*\bfirst?\b.*', re.IGNORECASE): 'first base',
    re.compile(r'.*\b2B?\b.*', re.IGNORECASE): 'second base',
    re.compile(r'.*\bsecond?\b.*', re.IGNORECASE): 'second base',
    re.compile(r'.*\b3B?\b.*', re.IGNORECASE): 'third base',
    re.compile(r'.*\bthird?\b.*', re.IGNORECASE): 'third base',
    re.compile(r'.*\bLF?\b.*', re.IGNORECASE): 'left field',
    re.compile(r'.*\bleft?\b.*', re.IGNORECASE): 'left field',
    re.compile(r'.*\bCF?\b.*', re.IGNORECASE): 'center field',
    re.compile(r'.*\bcenter?\b.*', re.IGNORECASE): 'center field',
    re.compile(r'.*\bRF?\b.*', re.IGNORECASE): 'right field',
    re.compile(r'.*\bright?\b.*', re.IGNORECASE): 'right field',
    re.compile(r'.*\bmiddle?\b.*', re.IGNORECASE): 'center field',
}

def map_location(location: str) -> str:
    """Map a location string to its corresponding standardized position."""
    for pattern, result in LOCATION_MAP.items():
        if pattern.match(location):
            return result
    return location 
    
    
    
def map_action(action: str) -> str:
    """Map an action string to its corresponding standardized action."""
    for pattern, result in ACTION_MAP.items():
        if pattern.match(action):
            return result
    return action  

