def game_analysis_prompt(game_info, player_data):
    if isinstance(game_info, dict):
        home_team = game_info.get('home_team', '')
        away_team = game_info.get('away_team', '')
        final_score = game_info.get('final_score', '0-0')
        innings_played = game_info.get('innings_played', 0)
        winner = game_info.get('winner', 'Tie')
    else:
        home_team = game_info.home_team
        away_team = game_info.away_team
        final_score = game_info.final_score
        innings_played = game_info.innings_played
        winner = game_info.winner
        
    prompt = f"""
    As a baseball analyst, provide a concise summary of this game between {home_team} and {away_team}. 
    Focus on key moments, notable player performances, and the flow of the game.
    
    Game Details:
    {home_team} vs {away_team}
    Final Score: {final_score}
    Innings: {innings_played}
    Winner: {winner}
    
    Player Performances:
    {player_data}
    """
    return prompt