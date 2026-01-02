"""
EXIF metadata extraction utilities for GPS coordinates.
Extracts GPS coordinates from image EXIF data.
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import io
from typing import Optional, Tuple, Dict


def get_exif_data(image: Image.Image) -> Optional[Dict]:
    """
    Extract EXIF data from PIL Image.
    
    Args:
        image: PIL Image object
        
    Returns:
        Dictionary of EXIF tags or None
    """
    try:
        exif_data = image._getexif()
        if exif_data is None:
            return None
        
        exif = {}
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            exif[tag] = value
        
        return exif
    except Exception as e:
        print(f"Error reading EXIF data: {e}")
        return None


def get_gps_data(exif_data: Dict) -> Optional[Dict]:
    """
    Extract GPS data from EXIF dictionary.
    
    Args:
        exif_data: Dictionary of EXIF tags
        
    Returns:
        Dictionary with GPS coordinates or None
    """
    if not exif_data or 'GPSInfo' not in exif_data:
        return None
    
    gps_info = {}
    for key, value in exif_data['GPSInfo'].items():
        tag = GPSTAGS.get(key, key)
        gps_info[tag] = value
    
    return gps_info


def convert_to_degrees(value: Tuple) -> float:
    """
    Convert GPS coordinate tuple to decimal degrees.
    
    Args:
        value: Tuple of (degrees, minutes, seconds) or (degrees, minutes)
        
    Returns:
        Decimal degrees as float
    """
    d, m, s = value[0], value[1], value[2] if len(value) > 2 else 0
    return float(d) + float(m) / 60.0 + float(s) / 3600.0


def get_lat_lon_from_exif(image: Image.Image) -> Optional[Tuple[float, float]]:
    """
    Extract latitude and longitude from image EXIF data.
    
    Args:
        image: PIL Image object
        
    Returns:
        Tuple of (latitude, longitude) in decimal degrees, or None
    """
    exif_data = get_exif_data(image)
    if not exif_data:
        return None
    
    gps_data = get_gps_data(exif_data)
    if not gps_data:
        return None
    
    try:
        lat = gps_data.get('GPSLatitude')
        lat_ref = gps_data.get('GPSLatitudeRef')
        lon = gps_data.get('GPSLongitude')
        lon_ref = gps_data.get('GPSLongitudeRef')
        
        if not all([lat, lat_ref, lon, lon_ref]):
            return None
        
        latitude = convert_to_degrees(lat)
        if lat_ref == 'S':
            latitude = -latitude
        
        longitude = convert_to_degrees(lon)
        if lon_ref == 'W':
            longitude = -longitude
        
        return (latitude, longitude)
    except Exception as e:
        print(f"Error parsing GPS coordinates: {e}")
        return None


def extract_gps_from_bytes(image_bytes: bytes) -> Optional[Tuple[float, float]]:
    """
    Extract GPS coordinates from image bytes.
    
    Args:
        image_bytes: Image file as bytes
        
    Returns:
        Tuple of (latitude, longitude) or None
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return get_lat_lon_from_exif(image)
    except Exception as e:
        print(f"Error extracting GPS from bytes: {e}")
        return None

