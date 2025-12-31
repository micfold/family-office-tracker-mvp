# config/settings.py

# Default Portfolio File Path
DEFAULT_PORTFOLIO_FILE = "Snowball Holdings.csv"  # The Snapshot
DEFAULT_HISTORY_FILE = "Snowball History.csv"     # The Transaction Log

# UI Categories for Manual Entry
UI_CATEGORIES = {
    "Income": ["Salary", "Dividends", "Business Income", "Refunds", "Other Income"],
    "Expense": [
        "Housing (Mortgage/Rent)", "Utilities", "Subscriptions", "Education", "Insurance",
        "Groceries", "Dining Out", "Transport (Fuel/Taxi)", "Health & Wellness",
        "Shopping", "Travel", "Services", "Family/Kids", "Other Expense"
    ],
    "Investment": ["Investment Deposit", "Investment Withdrawal"]
}

# Analytics Mapping (Category -> Type)
CATEGORY_TYPE_MAP = {
    "Salary": "Income", "Dividends": "Income", "Business Income": "Income",
    "Refunds": "Income", "Other Income": "Income",
    "Investment Deposit": "Investment", "Investment Withdrawal": "Investment",
    "Housing (Mortgage/Rent)": "Fixed", "Utilities": "Fixed",
    "Subscriptions": "Fixed", "Education": "Fixed", "Insurance": "Fixed",
    "Groceries": "Variable", "Dining Out": "Variable",
    "Transport (Fuel/Taxi)": "Variable", "Health & Wellness": "Variable",
    "Shopping": "Variable", "Travel": "Variable", "Services": "Variable",
    "Family/Kids": "Variable", "Other Expense": "Variable",
    "Uncategorized": "Variable"
}

# Global Categorization Rules
GLOBAL_RULES = [
    {'pattern': 'Trading 212', 'target': 'Investment Deposit'},
    {'pattern': 'XTB', 'target': 'Investment Deposit'},
    {'pattern': 'Hypoteka', 'target': 'Housing (Mortgage/Rent)'},
    {'pattern': 'Shell', 'target': 'Transport (Fuel/Taxi)'},
    {'pattern': 'Benzina', 'target': 'Transport (Fuel/Taxi)'},
    {'pattern': 'MOL', 'target': 'Transport (Fuel/Taxi)'},
    {'pattern': 'Uber', 'target': 'Transport (Fuel/Taxi)'},
    {'pattern': 'Bolt', 'target': 'Transport (Fuel/Taxi)'},
    {'pattern': 'Lekarna', 'target': 'Health & Wellness'},
    {'pattern': 'Dr. Max', 'target': 'Health & Wellness'},
    {'pattern': 'Albert', 'target': 'Groceries'},
    {'pattern': 'Tesco', 'target': 'Groceries'},
    {'pattern': 'Lidl', 'target': 'Groceries'},
    {'pattern': 'Kaufland', 'target': 'Groceries'},
    {'pattern': 'Rohlik', 'target': 'Groceries'},
    {'pattern': 'Netflix', 'target': 'Subscriptions'},
    {'pattern': 'Spotify', 'target': 'Subscriptions'},
    {'pattern': 'YouTube', 'target': 'Subscriptions'}
]