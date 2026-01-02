# src/views/utils/address_autocomplete.py
import streamlit as st
import requests
from config import GOOGLE_MAPS_API_KEY

def get_address_suggestions(input_text: str):
    """
    Fetches address suggestions from the Google Maps Places API.
    """
    if not input_text or not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY":
        return []

    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input_text}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("predictions", [])
    return []

def get_place_details(place_id: str):
    """
    Fetches details for a specific place from the Google Maps Places API.
    """
    if not place_id or not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY":
        return None

    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={GOOGLE_MAPS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get("result", None)
    return None

