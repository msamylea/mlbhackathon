from dataclasses import dataclass
from typing import List, Dict, Any
from services.game_statistics_models import GamePlayer, GameAtBatStats, GamePitchingStats
from prompts.analysis_prompt import game_analysis_prompt

@dataclass 
class LLMGameAnalysis:
    players: List[GamePlayer]
    game_info: Dict
    client: Any
    
    def to_dict(self) -> Dict:
        """Convert LLMGameAnalysis to dictionary"""
        return {
            "players": [player.to_dict() for player in self.players],
            "game_info": self.game_info.to_dict()
        }
        
    def __post_init__(self):
        """Initialize empty lists if not provided"""
        if not self.players:
            self.players = []
        if not self.game_info:
            raise ValueError("game_info must be provided")
            
    def add_player(self, player: GamePlayer):
        """Add player to analysis"""
        if not isinstance(player, GamePlayer):
            raise TypeError("player must be an instance of GamePlayer")
            
        new_player = GamePlayer(
            player_id=player.player_id,
            name=player.name,
            team=player.team,
            position=player.position
        )
        
        # Copy statistics if they exist
        if player.batting_stats:
            new_player.batting_stats = GameAtBatStats(**player.batting_stats.__dict__)
        if player.pitching_stats:
            new_player.pitching_stats = GamePitchingStats(**player.pitching_stats.__dict__)

        self.players.append(new_player)
    
    def send_to_llm(self) -> str:
        """Send game analysis to LLM and return the response"""
        prompt = game_analysis_prompt(
            game_info=self.game_info.to_dict(),
            player_data=[player.to_dict() for player in self.players]
        )
        
        response = self.client.get_response(prompt)
        return response