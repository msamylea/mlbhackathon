from typing import List, Dict, Optional
from dataclasses import dataclass
from manager.player_manager import Player
from data.data_loader import TeamDataLoader

@dataclass(frozen=True, eq=True)
class BatterProfile:
    """Represents a batter's key characteristics for lineup optimization"""
    player_id: int
    name: str
    position: str
    stats: Dict[str, any]  
    
    def __hash__(self):
        return hash((self.player_id, self.name, self.position))
    
    @property
    def obp(self) -> float:
        return float(self.stats.get('obp', 0.320))
        
    @property
    def slg(self) -> float:
        return float(self.stats.get('slg', 0.400))
        
    @property
    def hr(self) -> int:
        return int(self.stats.get('hr', 3))
    
    @property
    def hits(self) -> int:
        return int(self.stats.get('hits', 110))
        
    @property
    def rbi(self) -> int:
        return int(self.stats.get('rbi', 20))
        
    @property
    def avg(self) -> float:
        return float(self.stats.get('avg', 0.250))
    
    @property
    def ops(self) -> float:
        return float(self.stats.get('ops', 0.720))

class LineupOptimizer:
    """Optimizes batting order based on player statistics and historical baseball strategy"""
    
    def __init__(self):
        self.data_loader = TeamDataLoader()

    def _create_batter_profile(self, player: Player) -> Optional[BatterProfile]:
        """Create BatterProfile from Player object"""
        try:
            return BatterProfile(
                player_id=player.id,
                name=player.name,
                position=player.position,
                stats=player.batting_stats.to_dict() if player.batting_stats else {}
            )
        except Exception as e:
            return None

    def optimize_lineup(self, players: List[Player]) -> List[Player]:
        """Create optimized batting order using Player objects"""
        try:
            position_players = [p for p in players if p.position != 'P']
            
            profiles_with_players = []
            for player in position_players:
                profile = self._create_batter_profile(player)
                if profile:
                    profiles_with_players.append((profile, player))

            if len(profiles_with_players) < 9:
                
                return position_players  
                
            in_lineup = []
            available_profiles = profiles_with_players.copy()
            
            leadoff_idx = max(range(len(available_profiles)), 
                            key=lambda i: available_profiles[i][0].obp)
            in_lineup.append(available_profiles.pop(leadoff_idx))
            
            h2_idx = max(range(len(available_profiles)), 
                        key=lambda i: available_profiles[i][0].ops)
            in_lineup.append(available_profiles.pop(h2_idx))
            
            h3_idx = max(range(len(available_profiles)), 
                        key=lambda i: available_profiles[i][0].avg)
            in_lineup.append(available_profiles.pop(h3_idx))
            
            h4_idx = max(range(len(available_profiles)), 
                        key=lambda i: available_profiles[i][0].ops)
            in_lineup.append(available_profiles.pop(h4_idx))
            
            h5_idx = max(range(len(available_profiles)), 
                        key=lambda i: available_profiles[i][0].slg)
            in_lineup.append(available_profiles.pop(h5_idx))
            
            while available_profiles and len(in_lineup) < 9:
                next_idx = max(range(len(available_profiles)), 
                             key=lambda i: available_profiles[i][0].ops)
                in_lineup.append(available_profiles.pop(next_idx))
            
            return [player for _, player in in_lineup]
                
        except Exception as e:
            return position_players  
        
    def _create_default_lineup(self) -> List[Dict]:
        """Create a default lineup"""
        return [
            {
                'player': {'id': i, 'fullName': f'Position Player {i+1}'},
                'position': 'UTIL',
                'stats': {'avg': .250, 'slg': .400, 'ops': .720, 'hr': 3, 'rbi': 20, 'hits': 110}
            }
            for i in range(9)
        ]