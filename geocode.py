"""
Reverse geocoding utilities using OpenStreetMap Nominatim API.
Converts GPS coordinates to place names.
"""

import requests
from typing import Optional, Dict
import time


class Geocoder:
    """Reverse geocoding using Nominatim API."""
    
    def __init__(self, user_agent: str = "GeoGenie/1.0"):
        """
        Initialize geocoder.
        
        Args:
            user_agent: User agent string for Nominatim API (required)
        """
        self.base_url = "https://nominatim.openstreetmap.org/reverse"
        self.user_agent = user_agent
        self.headers = {
            "User-Agent": self.user_agent
        }
        # Rate limiting: Nominatim allows 1 request per second
        self.last_request_time = 0
        self.min_interval = 1.0
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Reverse geocode coordinates to place name.
        
        Args:
            lat: Latitude in decimal degrees
            lon: Longitude in decimal degrees
            
        Returns:
            Dictionary with place information or None
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_interval:
            time.sleep(self.min_interval - time_since_last)
        
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": 1
            }
            
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            self.last_request_time = time.time()
            
            # Extract place name from response
            address = data.get("address", {})
            place_name = (
                address.get("tourism") or  # For landmarks
                address.get("historic") or
                address.get("attraction") or
                address.get("name") or
                address.get("building") or
                data.get("display_name", "").split(",")[0]  # Fallback to first part of display name
            )
            
            return {
                "place_name": place_name,
                "full_address": data.get("display_name", ""),
                "raw_data": data
            }
        except requests.exceptions.RequestException as e:
            print(f"Geocoding error: {e}")
            return None
        except Exception as e:
            print(f"Error processing geocoding response: {e}")
            return None


# Global instance
_geocoder = None


def get_geocoder() -> Geocoder:
    """Get or create global geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = Geocoder()
    return _geocoder

