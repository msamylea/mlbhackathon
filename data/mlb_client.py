from typing import Dict, Optional
import httpx
from functools import lru_cache
from tenacity import retry, stop_after_attempt


class MLBDataClient():
    def __init__(self, timeout: float = 30.0):
        self.base_url = "https://statsapi.mlb.com/api/v1"
        self.client = httpx.Client(timeout=timeout)

    @lru_cache(maxsize=128)
    def get_venue_details(self, team_id: int, year: int) -> Dict:
        """Get venue details for a specific venue"""
        team_data = self.get_team_details(team_id, year)
        team_info = team_data['teams'][0]
        venue_id = team_info['venue']['id']
        url = f"{self.base_url}/venues?venueIds={venue_id}&hydrate=location,fieldInfo"
        response = self._make_request(url, {})
        return response
    
    
    @lru_cache(maxsize=128)
    def get_stats(self, player_id: int, year: int) -> Dict:
        url = f"{self.base_url}/people/{player_id}"
        params = {
            "season": year,
            "hydrate": f"stats(group=[hitting,pitching],type=[career,statSplits,metricAverages,careerAdvanced],metrics=[launchSpeed,distance,launchAngle,releaseSpeed],sitCodes=[vr,vl],season={year})"
        }
        
        response = self._make_request(url, params)
        
        
        return response
    
    @lru_cache(maxsize=128)
    def get_team_roster(self, team_id: int, season: int) -> Dict:
        """Get raw team roster data"""
        
        url = f"{self.base_url}/teams/{team_id}/roster"
        params = {
            "season": season,
            "rosterType": "fullSeason"
        }
        
        response = self._make_request(url, params)
        return response
            
       
        
    @lru_cache(maxsize=128)
    def get_team_details(self, team_id: int, year: int) -> Dict:
        """Get team details including first year of play and venue"""
        try:
            url = f"{self.base_url}/teams/{team_id}?season={year}"
            params = {
                "hydrate": "venue", 
                "fields": "teams,id,name,firstYearOfPlay,venue"
            }
            
            response = self._make_request(url, params)

            return response
            
        except Exception as e:
            raise ValueError(f"Error fetching team details for {team_id}: {e}")
            
    @lru_cache(maxsize=128)
    def get_pitchers(self, team_id, year: int) -> Dict:
    
        url = f"{self.base_url}/teams/{team_id}/leaders?leaderCategories=inningsPitched&season={year}"
        params = {
            "season": year, 
        }
        
        response = self._make_request(url, params)

        return response
           
    @lru_cache(maxsize=128)
    def get_pitch_arsenal(self, pitcher_id, year: int) -> Dict:
        """Get a pitcher's pitch arsenal for a specific season"""
        url = f"{self.base_url}/people/{pitcher_id}"
        params = {
            "season": year,
            "hydrate": f"stats(group=[pitching],type=[pitchArsenal,career],season={year})"
        }
        
        response = self._make_request(url, params)
        return response

    @lru_cache(maxsize=128)
    @retry(stop=(stop_after_attempt(3)))
    def get_roster_with_stats(self, team_id: int, year: int) -> Dict:
        """Get team roster with player stats"""
        url=f"{self.base_url}/teams/{team_id}/roster?rosterType=Active&season={year}&hydrate=person(stats(group=[hitting,pitching],type=[career,careerAdvanced,metricAverages,sabermetrics],metrics=[launchSpeed,distance,launchAngle,releaseSpeed])%3A%29"

        response = self.client.get(url)
        response.raise_for_status() 
        return response.json()      
    

    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        try:
            response = self.client.get(url, params=params)
            response.raise_for_status() 
            return response.json()
        
        except Exception as e:
            raise ValueError(f"Error fetching data from {url}: {e}")