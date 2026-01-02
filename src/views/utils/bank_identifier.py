# src/views/utils/bank_identifier.py
import re

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

