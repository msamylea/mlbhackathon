import pandas as pd
import json
from typing import Dict, Tuple, Union
from stats.base_stats import BattingStats, PitchingStats
import traceback

def get_league_baseline(year: int) -> Dict[str, Dict[str, float]]:
    """Get baseline stats for given year using league-wide totals"""
    hitting_stats, pitching_stats = get_historical_team_stats(year)
    
    baselines = {
        'hitting': {},
        'pitching': {}
    }
    
    if not hitting_stats.empty:
        pa = hitting_stats['plate_appearances'].iloc[0]
        hits = hitting_stats['hits'].iloc[0]
        
        if pa > 0:
            baselines['hitting'].update({
                'pa_per_game': pa / hitting_stats['games_played'].iloc[0] if hitting_stats['games_played'].iloc[0] > 0 else 0,
                'hits_per_pa': hits / pa,
                'bb_per_pa': hitting_stats['walks'].iloc[0] / pa,
                'k_per_pa': hitting_stats['strikeouts'].iloc[0] / pa,
                'ab_per_pa': hitting_stats['at_bats'].iloc[0] / pa,
                'sf_per_pa': hitting_stats['sac_flies'].iloc[0] / pa,
            })
            
            if hits > 0:
                baselines['hitting'].update({
                    'singles_per_hit': hitting_stats['singles'].iloc[0] / hits,
                    'doubles_per_hit': hitting_stats['doubles'].iloc[0] / hits,
                    'triples_per_hit': hitting_stats['triples'].iloc[0] / hits,
                    'hr_per_hit': hitting_stats['home_runs'].iloc[0] / hits,
                })
    
    if not pitching_stats.empty:
        bf = pitching_stats['batters_faced'].iloc[0]
        hits = pitching_stats['hits'].iloc[0]
        
        if bf > 0:
            baselines['pitching'].update({
                'bf_per_game': bf / pitching_stats['games_played'].iloc[0] if pitching_stats['games_played'].iloc[0] > 0 else 0,
                'hits_per_bf': hits / bf,
                'bb_per_bf': pitching_stats['walks'].iloc[0] / bf,
                'k_per_bf': pitching_stats['strikeouts'].iloc[0] / bf,
                'ab_per_bf': pitching_stats['at_bats'].iloc[0] / bf,
                'sf_per_bf': pitching_stats['sac_flies'].iloc[0] / bf,
            })
            
            if hits > 0:
                baselines['pitching'].update({
                    'singles_per_hit': pitching_stats['singles'].iloc[0] / hits,
                    'doubles_per_hit': pitching_stats['doubles'].iloc[0] / hits,
                    'triples_per_hit': pitching_stats['triples'].iloc[0] / hits,
                    'hr_per_hit': pitching_stats['home_runs'].iloc[0] / hits,
                })
    
    return baselines

def normalize_player_stats(player_stats: Union[BattingStats, PitchingStats, Dict], league_baseline: Dict, position: str) -> Dict:
    """Normalize player stats to league baseline while maintaining player's relative ratios"""
    try:
        stats_type = 'pitching' if position == 'P' else 'hitting'
        baseline = league_baseline[stats_type]
        normalized = {}
        
        if position == 'P':
            bf = player_stats.batters_faced
            innings = float(str(player_stats.innings_pitched).split('.')[0])  
            
            normalized_hits = round(bf * baseline['hits_per_bf'])
            normalized_walks = round(bf * baseline['bb_per_bf'])
            normalized_strikeouts = round(bf * baseline['k_per_bf'])
            
            total_hits = player_stats.hits
            normalized.update({
                'games_played': player_stats.games_played,
                'batters_faced': bf,
                'innings_pitched': player_stats.innings_pitched,
                'at_bats': round(bf * baseline['ab_per_bf']),
                'hits': normalized_hits,
                'walks': normalized_walks,
                'strikeouts': normalized_strikeouts,
                'sac_flies': round(bf * baseline['sf_per_bf'])
            })
            
            if total_hits > 0:
                hit_ratios = {
                    'singles': player_stats.singles / total_hits,
                    'doubles': player_stats.doubles / total_hits,
                    'triples': player_stats.triples / total_hits,
                    'home_runs': player_stats.home_runs / total_hits
                }
                
                normalized.update({
                    'singles': round(normalized_hits * hit_ratios['singles']),
                    'doubles': round(normalized_hits * hit_ratios['doubles']),
                    'triples': round(normalized_hits * hit_ratios['triples']),
                    'home_runs': round(normalized_hits * hit_ratios['home_runs'])
                })
                
            if innings > 0:
                runs = round((normalized_hits + normalized_walks) * 0.13 * 9)  
                normalized['era'] = round(runs / innings * 9, 2)
                normalized['whip'] = round((normalized_hits + normalized_walks) / innings, 3)
                normalized['xfip'] = round(((13 * normalized['home_runs']) + 
                                          (3 * (normalized_walks + normalized_strikeouts))) / bf, 3)
                normalized['babip'] = round((normalized_hits - normalized['home_runs']) / 
                                         (normalized['at_bats'] - normalized_strikeouts - 
                                          normalized['home_runs'] + normalized['sac_flies']), 3)
        else:
            pa = player_stats.plate_appearances
            
            normalized_hits = round(pa * baseline['hits_per_pa'])
            
            normalized.update({
                'games_played': player_stats.games_played,
                'plate_appearances': pa,
                'at_bats': round(pa * baseline['ab_per_pa']),
                'hits': normalized_hits,
                'walks': round(pa * baseline['bb_per_pa']),
                'strikeouts': round(pa * baseline['k_per_pa']),
                'sac_flies': round(pa * baseline['sf_per_pa'])
            })
            
            if player_stats.hits > 0:
                hit_ratios = {
                    'singles': player_stats.singles / player_stats.hits,
                    'doubles': player_stats.doubles / player_stats.hits,
                    'triples': player_stats.triples / player_stats.hits,
                    'home_runs': player_stats.home_runs / player_stats.hits
                }
                
                normalized.update({
                    'singles': round(normalized_hits * hit_ratios['singles']),
                    'doubles': round(normalized_hits * hit_ratios['doubles']),
                    'triples': round(normalized_hits * hit_ratios['triples']),
                    'home_runs': round(normalized_hits * hit_ratios['home_runs'])
                })
            
        return normalized
        
    except Exception as e:
       
        return {}

def process_data() -> pd.DataFrame:
    with open('sim_utils/raw_data.json', 'r') as f:
        data = json.load(f)

    df_list = []

    for team in data:
        team_name = team['team']['name']
        team_id = team['team']['id']
        stat_type = team['team']['stat_type']
        year = team['team']['year']
        stats = team['team']['stats']
        

        if stat_type == 'hitting':
            games_played = stats.get('gamesPlayed', 0)
            at_bats = stats.get('atBats', 0)
            sac_flies = stats.get('sacFlies', 0)
            hits = stats.get('hits', 0)
            runs = stats.get('runs', 0)
            doubles = stats.get('doubles', 0)
            triples = stats.get('triples', 0)
            home_runs = stats.get('homeRuns', 0)
            walks = stats.get('baseOnBalls', 0)
            strikeouts = stats.get('strikeOuts', 0)
            singles = hits - (doubles + triples + home_runs)
            plate_appearances = stats.get('plateAppearances', 0)
            innings_pitched = 0
            batters_faced = 0
            era = 0
            whip = 0
            
        elif stat_type == 'pitching':
            games_played = stats.get('gamesPlayed', 0)
            at_bats = stats.get('atBats', 0)
            sac_flies = stats.get('sacFlies', 0)
            hits = stats.get('hits', 0)
            runs = stats.get('runs', 0)
            innings_pitched = stats.get('inningsPitched', '0.0')
            
            doubles = stats.get('doubles', 0)
            
        
            triples = stats.get('triples', 0)
            
             
            home_runs = stats.get('homeRuns', 0)
            
            runs = stats.get('runs', 0)
       
            singles = hits - (doubles + triples + home_runs)
            era = stats.get('era', '0.00')
            whip = stats.get('whip', '0.00')
            walks = stats.get('baseOnBalls', 0)
            strikeouts = stats.get('strikeOuts', 0)
            plate_appearances = 0
           
            batters_faced = stats.get('battersFaced', 0)
            
           
        else:
            continue

        partial_df = pd.DataFrame({
            'team_name': [team_name],
            'team_id': [team_id],
            'stat_type': [stat_type],
            'year': [year],
            'games_played': [games_played],
            'hits': [hits],
            'runs': [runs],
            'singles': [singles],
            'doubles': [doubles],
            'triples': [triples],
            'home_runs': [home_runs],
            'era': [era],
            'whip': [whip],
            'walks': [walks],
            'at_bats': [at_bats],
            'sac_flies': [sac_flies],
            'strikeouts': [strikeouts],
            'plate_appearances': [plate_appearances],
            'batters_faced': [batters_faced],
            'innings_pitched': [innings_pitched]
        })

        df_list.append(partial_df)

    full_df = pd.concat(df_list, ignore_index=True)
    full_df = full_df.drop(['team_name', 'team_id'], axis=1)
    
    numeric_cols = ['hits', 'runs', 'at_bats', 'sac_flies', 'singles', 'doubles', 
                   'triples', 'home_runs', 'era', 'whip', 'walks', 'strikeouts', 
                   'plate_appearances', 'batters_faced', 'innings_pitched', 'games_played']
    
    full_df[numeric_cols] = full_df[numeric_cols].apply(pd.to_numeric)
    
    agg_dict = {
        'hits': 'sum',
        'runs': 'sum',
        'at_bats': 'sum',
        'sac_flies': 'sum',
        'singles': 'sum',
        'doubles': 'sum',
        'triples': 'sum',
        'home_runs': 'sum',
        'walks': 'sum',
        'strikeouts': 'sum',
        'plate_appearances': 'sum',
        'batters_faced': 'sum',
        'games_played': 'sum',
        'innings_pitched': 'sum',
        'era': 'mean', 
        'whip': 'mean'
    }
    
    full_df = full_df.groupby(['year', 'stat_type'], as_index=False).agg(agg_dict)
    
    return full_df

def get_historical_team_stats(year_input) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Get hitting and pitching stats for year"""
    try:
        if hasattr(year_input, 'year'):
            year = int(year_input.year)
        else:
            year = int(year_input)
            
        data = process_data()
        data['year'] = data['year'].astype(int)
        
        year_stats = data[data['year'] == year]
        if year_stats.empty:
            return pd.DataFrame(), pd.DataFrame()
            
        hitting_stats = year_stats[year_stats['stat_type'] == 'hitting']
        pitching_stats = year_stats[year_stats['stat_type'] == 'pitching']
        
        if hitting_stats.empty:
            raise ValueError(f"No hitting stats found for {year}")
        if pitching_stats.empty:
            raise ValueError(f"No pitching stats found for {year}")
            
        return hitting_stats, pitching_stats
        
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()
    
def get_league_rates(year: int, stats, position) -> Dict[str, float]:
    try:
        baselines = get_league_baseline(year)
        normalized_player = normalize_player_stats(stats, baselines, position)
        
        if position == 'P':
            bf = float(normalized_player.get('batters_faced', 0))
            innings = float(stats.__dict__.get('innings_pitched', bf/3))  
            normalized_player['innings_pitched'] = innings  
            
            if innings > 0:
                hits = float(normalized_player.get('hits', 0))
                walks = float(normalized_player.get('walks', 0))
                runs = (walks + hits) * 0.5  
                
                normalized_player['era'] = round(9.0 * (runs / innings), 2)
                normalized_player['whip'] = round((hits + walks) / innings, 3)
            
      
            ab = float(normalized_player.get('at_bats', 0))
            ab_for_babip = ab - normalized_player.get('strikeouts', 0) - normalized_player.get('home_runs', 0) + normalized_player.get('sac_flies', 0)
            if ab_for_babip > 0:
                hits = float(normalized_player.get('hits', 0))
                normalized_player['babip'] = round((hits - normalized_player.get('home_runs', 0)) / ab_for_babip, 3)
                
        else:
            ab = float(normalized_player.get('at_bats', 0))
            pa = float(normalized_player.get('plate_appearances', 0))
            hits = float(normalized_player.get('hits', 0))
            
            if ab > 0:
                normalized_player['avg'] = hits / ab
                normalized_player['slg'] = (normalized_player['singles'] + 
                                          (2 * normalized_player['doubles']) + 
                                          (3 * normalized_player['triples']) + 
                                          (4 * normalized_player['home_runs'])) / ab
            
            if pa > 0:
                walks = float(normalized_player.get('walks', 0))
                normalized_player['obp'] = (hits + walks) / pa
                
            if 'obp' in normalized_player and 'slg' in normalized_player:
                normalized_player['ops'] = normalized_player['obp'] + normalized_player['slg']
                
            ab_for_babip = ab - normalized_player.get('strikeouts', 0) - normalized_player.get('home_runs', 0) + normalized_player.get('sac_flies', 0)
            if ab_for_babip > 0:
                normalized_player['babip'] = (hits - normalized_player.get('home_runs', 0)) / ab_for_babip
        
        normalized_player = {k: round(float(v), 3) for k,v in normalized_player.items()}
        return normalized_player
            
    except Exception as e:
        return None