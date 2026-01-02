# src/core/maps_helper.py
"""
Google Maps API helper functions for address autocomplete and static map generation.
"""
import logging
import streamlit as st
from typing import Optional, Dict, List, Tuple
from decimal import Decimal

# Get logger for this module
logger = logging.getLogger(__name__)


def get_google_maps_api_key() -> Optional[str]:
    """
    Retrieve Google Maps API key from Streamlit secrets.
    
    Returns:
        API key string if found, None otherwise
    """
    try:
        api_key = st.secrets.get("google_maps", {}).get("api_key")
        if api_key and api_key != "YOUR_GOOGLE_MAPS_API_KEY_HERE":
            logger.info("Google Maps API key loaded successfully")
            return api_key
        else:
            logger.warning("Google Maps API key not configured in .streamlit/secrets.toml")
            return None
    except Exception as e:
        logger.error(f"Error loading Google Maps API key: {e}")
        return None


def get_address_suggestions(query: str, api_key: str) -> List[Dict[str, str]]:
    """
    Get address suggestions from Google Places Autocomplete API.
    
    Args:
        query: The partial address string to search for
        api_key: Google Maps API key
        
    Returns:
        List of dictionaries containing place_id and description
    """
    if not query or len(query) < 3:
        logger.debug(f"Query too short: '{query}'")
        return []
    
    try:
        import googlemaps
        logger.debug(f"Fetching address suggestions for query: '{query}'")
        
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.places_autocomplete(
            input_text=query,
            types=['address']
        )
        
        suggestions = [
            {
                'place_id': prediction['place_id'],
                'description': prediction['description']
            }
            for prediction in result
        ]
        
        logger.info(f"Found {len(suggestions)} address suggestions for query: '{query}'")
        return suggestions
        
    except ImportError:
        logger.error("googlemaps library not installed. Run: pip install googlemaps")
        return []
    except Exception as e:
        logger.error(f"Error fetching address suggestions: {e}", exc_info=True)
        return []


def get_place_details(place_id: str, api_key: str) -> Optional[Dict]:
    """
    Get detailed information about a place including coordinates.
    
    Args:
        place_id: Google Place ID
        api_key: Google Maps API key
        
    Returns:
        Dictionary containing address, latitude, and longitude
    """
    try:
        import googlemaps
        logger.debug(f"Fetching place details for place_id: {place_id}")
        
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.place(place_id=place_id)
        
        if result.get('status') == 'OK':
            place = result.get('result', {})
            location = place.get('geometry', {}).get('location', {})
            
            details = {
                'address': place.get('formatted_address', ''),
                'latitude': Decimal(str(location.get('lat', 0))),
                'longitude': Decimal(str(location.get('lng', 0)))
            }
            
            logger.info(f"Place details retrieved: {details['address']}")
            return details
        else:
            logger.warning(f"Place details request failed with status: {result.get('status')}")
            return None
            
    except ImportError:
        logger.error("googlemaps library not installed. Run: pip install googlemaps")
        return None
    except Exception as e:
        logger.error(f"Error fetching place details: {e}", exc_info=True)
        return None


def get_static_map_url(latitude: float, longitude: float, api_key: str, 
                       width: int = 400, height: int = 300, zoom: int = 15) -> str:
    """
    Generate a Google Maps Static API URL for a location.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        api_key: Google Maps API key
        width: Map image width in pixels
        height: Map image height in pixels
        zoom: Map zoom level (1-20)
        
    Returns:
        URL string for the static map image
    """
    try:
        url = (
            f"https://maps.googleapis.com/maps/api/staticmap?"
            f"center={latitude},{longitude}"
            f"&zoom={zoom}"
            f"&size={width}x{height}"
            f"&markers=color:red%7C{latitude},{longitude}"
            f"&key={api_key}"
        )
        logger.debug(f"Generated static map URL for location: ({latitude}, {longitude})")
        return url
    except Exception as e:
        logger.error(f"Error generating static map URL: {e}", exc_info=True)
        return ""
