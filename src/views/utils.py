# src/views/utils.py

def format_currency(amount: float, currency: str) -> str:
    """
    Formats a number as a currency string with a space as a thousand separator and a comma as a decimal separator.
    """
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",")

CURRENCY_ICONS = {
    "USD": "🇺🇸", "EUR": "🇪🇺", "CZK": "🇨🇿", "GBP": "🇬🇧",
    "JPY": "🇯🇵", "AUD": "🇦🇺", "CAD": "🇨🇦", "CHF": "🇨🇭",
    "CNY": "🇨🇳", "SEK": "🇸🇪", "NZD": "🇳🇿",
}

def get_currency_icon(currency_code: str) -> str:
    """Returns a unicode flag icon for a given currency code."""
    return CURRENCY_ICONS.get(currency_code, "💰")


import re
import logging

logger = logging.getLogger(__name__)

# A simple dictionary mapping Czech bank codes to their names.
# This can be expanded or moved to a database in a real application.
CZECH_BANK_CODES = {
    "0100": "Komerční banka",
    "0300": "ČSOB",
    "0600": "MONETA Money Bank",
    "0710": "ČNB",
    "0800": "Česká spořitelna",
    "2010": "Fio banka",
    "2250": "Revolut Bank",
    "2600": "Citibank",
    "2700": "UniCredit Bank",
    "3030": "Air Bank",
    "5500": "Raiffeisenbank",
    "6210": "mBank",
}

def identify_bank(account_identifier: str) -> str:
    """
    Identifies the bank from a Czech bank account number or an IBAN.
    Returns the bank name or "Unknown Bank" if not found.
    """
    if not account_identifier:
        return ""

    # Case 1: Standard Czech format (e.g., "123456789/0800")
    match = re.search(r'/(\d{4})$', account_identifier)
    if match:
        bank_code = match.group(1)
        return CZECH_BANK_CODES.get(bank_code, "Unknown Bank")

    # Case 2: IBAN format (e.g., "CZ6508000000000000000000")
    # The bank code is typically in characters 5-8 for CZ IBANs.
    if account_identifier.upper().startswith("CZ") and len(account_identifier) >= 8:
        bank_code = account_identifier[4:8]
        return CZECH_BANK_CODES.get(bank_code, "Unknown Bank")

    return "Unknown Bank"


from datetime import datetime, date
from decimal import Decimal

def calculate_vehicle_amortization(
    acquisition_price: Decimal,
    year_made: int,
    kilometers_driven: int,
    current_year: int = None
) -> Decimal:
    """
    Calculates the estimated current market value of a vehicle based on age and mileage.
    """
    if current_year is None:
        current_year = datetime.now().year

    age = max(0, current_year - year_made)

    # 1. Age-based depreciation (e.g., 15% per year)
    age_depreciation_rate = Decimal("0.15")
    age_depreciation = acquisition_price * (age_depreciation_rate * age)

    # 2. Mileage-based depreciation (e.g., $0.10 per km)
    mileage_depreciation_rate = Decimal("0.10")
    mileage_depreciation = Decimal(kilometers_driven) * mileage_depreciation_rate

    # Total depreciation
    total_depreciation = age_depreciation + mileage_depreciation

    # Ensure value doesn't go below a minimum (e.g., 10% of original value)
    minimum_value = acquisition_price * Decimal("0.10")

    estimated_value = max(minimum_value, acquisition_price - total_depreciation)

    return estimated_value.quantize(Decimal('0.01'))


def calculate_czech_mortgage_deduction(
    start_date: date,
    annual_interest_paid: Decimal,
    tax_region: str
) -> Decimal:
    """
    Calculates the tax-deductible interest for a mortgage in the Czech Republic.
    """
    if tax_region != "Czech Republic":
        return Decimal("0.0")

    limit = Decimal("300000") if start_date.year < 2021 else Decimal("150000")

    return min(annual_interest_paid, limit)


import requests
import streamlit as st

def get_address_suggestions(input_text: str):
    """
    Fetches address suggestions from the Google Maps Places API.
    """
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY")

    if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
        logger.warning("Google Maps API key is not configured. Address search will be disabled.")
        return []

    if not input_text:
        logger.debug("Address search input is empty, not calling API.")
        return []

    logger.info(f"Requesting address suggestions for input: '{input_text}'")
    url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input={input_text}&key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
        logger.debug(f"Google Maps API response: {response.text}")
        predictions = response.json().get("predictions", [])
        logger.info(f"Found {len(predictions)} address suggestions.")
        return predictions
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Google Maps Autocomplete API: {e}")
        return []

def get_place_details(place_id: str):
    """
    Fetches details for a specific place from the Google Maps Places API.
    """
    api_key = st.secrets.get("GOOGLE_MAPS_API_KEY")

    if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
        logger.warning("Google Maps API key is not configured. Cannot fetch place details.")
        return None

    if not place_id:
        logger.debug("Place ID is empty, not calling API.")
        return None

    logger.info(f"Requesting place details for place_id: '{place_id}'")
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        logger.debug(f"Google Maps Place Details API response: {response.text}")
        result = response.json().get("result", None)
        if result:
            logger.info(f"Successfully fetched details for place: {result.get('name')}")
        else:
            logger.warning(f"No details found for place_id: {place_id}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Google Maps Place Details API: {e}")
        return None

