from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class VenueData:
    """Contains relevant venue information for hit calculations"""
    name: str
    left_line: Optional[int] = 332
    left_center: Optional[int] = 375
    center: Optional[int] = 405
    right_center: Optional[int] = 375
    right_line: Optional[int] = 329
    elevation: Optional[int] = 600
    turf_type: Optional[str] = 'grass'
    roof_type: Optional[str] = 'open'

    @classmethod
    def from_api_response(cls, venue_data: Dict) -> 'VenueData':
        venue_info = venue_data.get('venues', [{}])[0]
        field_info = venue_info.get('fieldInfo', {})
        
        return cls(
            name=venue_info.get('name', 'Unknown Venue'),
            left_line=field_info.get('leftLine', cls.left_line),
            left_center=field_info.get('leftCenter', cls.left_center),
            center=field_info.get('center', cls.center),
            right_center=field_info.get('rightCenter', cls.right_center),
            right_line=field_info.get('rightLine', cls.right_line),
            elevation=venue_info.get('location', {}).get('elevation', cls.elevation),
            turf_type=field_info.get('turfType', cls.turf_type),
            roof_type=field_info.get('roofType', cls.roof_type)
        )

    def get_venue_data(self) -> Dict:
        """Return venue data as a dictionary"""
        return {
            'name': self.name,
            'left_line': self.left_line,
            'left_center': self.left_center,
            'center': self.center,
            'right_center': self.right_center,
            'right_line': self.right_line,
            'elevation': self.elevation,
            'turf_type': self.turf_type,
            'roof_type': self.roof_type
        }