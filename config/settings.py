# config/settings.py

# Default Portfolio File Path
DEFAULT_PORTFOLIO_FILE = "Snowball Holdings.csv"

# 2. Analytics Mapping (Maps Category -> Fixed/Variable/Income)
# This controls the "Fixed vs Variable" chart automatically
CATEGORY_TYPE_MAP = {
    # Income
    "Salary": "Income", "Dividends": "Income", "Business Income": "Income",
    "Refunds": "Income", "Other Income": "Income",

    # Investment
    "Investment Deposit": "Investment", "Investment Withdrawal": "Investment",

    # Fixed Expenses
    "Housing (Mortgage/Rent)": "Fixed",
    "Utilities": "Fixed",
    "Subscriptions": "Fixed",
    "Education": "Fixed",
    "Insurance": "Fixed",

    # Variable Expenses
    "Groceries": "Variable",
    "Dining Out": "Variable",
    "Transport (Fuel/Taxi)": "Variable",
    "Health & Wellness": "Variable",
    "Shopping": "Variable",
    "Travel": "Variable",
    "Services": "Variable",
    "Family/Kids": "Variable",
    "Other Expense": "Variable",

    # Default
    "Uncategorized": "Variable"
}

# 3. Global Rules (Updated to match new Category names)
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