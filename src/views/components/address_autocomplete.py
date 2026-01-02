# src/views/components/address_autocomplete.py
"""
Address autocomplete component with Google Maps Places API integration.
"""
import streamlit as st
import logging
from typing import Optional, Dict, Tuple
from decimal import Decimal

from src.core.maps_helper import (
    get_google_maps_api_key,
    get_address_suggestions,
    get_place_details,
    get_static_map_url
)

logger = logging.getLogger(__name__)


def render_address_input_with_autocomplete(
    label: str = "Address",
    key_prefix: str = "address",
    default_value: str = "",
    default_lat: Optional[Decimal] = None,
    default_lng: Optional[Decimal] = None
) -> Tuple[str, Optional[Decimal], Optional[Decimal]]:
    """
    Render an address input field with Google Places autocomplete and map preview.
    
    Args:
        label: Label for the address input field
        key_prefix: Unique prefix for session state keys
        default_value: Default address value
        default_lat: Default latitude
        default_lng: Default longitude
        
    Returns:
        Tuple of (address, latitude, longitude)
    """
    # Initialize session state keys
    address_key = f"{key_prefix}_address"
    lat_key = f"{key_prefix}_lat"
    lng_key = f"{key_prefix}_lng"
    query_key = f"{key_prefix}_query"
    selected_key = f"{key_prefix}_selected"
    
    if address_key not in st.session_state:
        st.session_state[address_key] = default_value
    if lat_key not in st.session_state:
        st.session_state[lat_key] = default_lat
    if lng_key not in st.session_state:
        st.session_state[lng_key] = default_lng
    if query_key not in st.session_state:
        st.session_state[query_key] = default_value
    if selected_key not in st.session_state:
        st.session_state[selected_key] = False
    
    # Get API key
    api_key = get_google_maps_api_key()
    
    if not api_key:
        st.warning("⚠️ Google Maps API key not configured. Please add your API key to `.streamlit/secrets.toml`")
        address = st.text_input(label, value=default_value, key=f"{key_prefix}_fallback")
        logger.warning("Google Maps API key not available, using fallback text input")
        return address, None, None
    
    # Address input with real-time suggestions
    query = st.text_input(
        label,
        value=st.session_state[query_key],
        key=f"{key_prefix}_input",
        help="Start typing to see address suggestions",
        placeholder="Start typing an address..."
    )
    
    # Update query in session state
    if query != st.session_state[query_key]:
        st.session_state[query_key] = query
        st.session_state[selected_key] = False
        logger.debug(f"Query updated to: '{query}'")
    
    # Fetch suggestions when query changes and has enough characters
    if query and len(query) >= 3 and not st.session_state[selected_key]:
        try:
            suggestions = get_address_suggestions(query, api_key)
            
            if suggestions:
                logger.debug(f"Displaying {len(suggestions)} suggestions")
                
                # Display suggestions as selectbox
                suggestion_options = ["Select an address..."] + [s['description'] for s in suggestions]
                
                selected_option = st.selectbox(
                    "Select from suggestions:",
                    options=suggestion_options,
                    key=f"{key_prefix}_selectbox"
                )
                
                # When user selects an address
                if selected_option != "Select an address...":
                    # Find the selected suggestion
                    selected_suggestion = next(
                        (s for s in suggestions if s['description'] == selected_option),
                        None
                    )
                    
                    if selected_suggestion:
                        logger.info(f"User selected address: {selected_option}")
                        
                        # Fetch place details
                        with st.spinner("Loading location details..."):
                            details = get_place_details(selected_suggestion['place_id'], api_key)
                        
                        if details:
                            # Update session state with selected address
                            st.session_state[address_key] = details['address']
                            st.session_state[lat_key] = details['latitude']
                            st.session_state[lng_key] = details['longitude']
                            st.session_state[query_key] = details['address']
                            st.session_state[selected_key] = True
                            
                            logger.info(f"Address details saved: {details['address']}")
                            st.success(f"✅ Address selected: {details['address']}")
                            st.rerun()
            else:
                if len(query) >= 3:
                    st.info("No address suggestions found. Try a different search term.")
                    logger.debug(f"No suggestions found for query: '{query}'")
        except Exception as e:
            st.error(f"Error fetching address suggestions: {str(e)}")
            logger.error(f"Error in address autocomplete: {e}", exc_info=True)
    
    # Display map if coordinates are available
    if st.session_state[lat_key] and st.session_state[lng_key]:
        try:
            lat = float(st.session_state[lat_key])
            lng = float(st.session_state[lng_key])
            
            st.markdown("**📍 Location Preview:**")
            map_url = get_static_map_url(lat, lng, api_key, width=600, height=200, zoom=15)
            
            if map_url:
                st.image(map_url, use_container_width=True)
                logger.debug(f"Displaying map for coordinates: ({lat}, {lng})")
            else:
                logger.warning("Failed to generate map URL")
                
        except Exception as e:
            logger.error(f"Error displaying map: {e}", exc_info=True)
    
    # Return the current values
    return (
        st.session_state[address_key],
        st.session_state[lat_key],
        st.session_state[lng_key]
    )


def display_location_map(latitude: Decimal, longitude: Decimal, width: int = 600, height: int = 200):
    """
    Display a static map for a given location.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        width: Map width in pixels
        height: Map height in pixels
    """
    api_key = get_google_maps_api_key()
    
    if not api_key:
        logger.warning("Cannot display map - API key not configured")
        return
    
    try:
        lat = float(latitude)
        lng = float(longitude)
        
        map_url = get_static_map_url(lat, lng, api_key, width=width, height=height, zoom=15)
        
        if map_url:
            st.image(map_url, use_container_width=True)
            logger.debug(f"Displayed map for coordinates: ({lat}, {lng})")
        else:
            logger.warning("Failed to generate map URL")
            
    except Exception as e:
        logger.error(f"Error displaying location map: {e}", exc_info=True)
