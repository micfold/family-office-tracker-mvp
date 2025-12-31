# config/settings.py

# Default Portfolio File Path
DEFAULT_PORTFOLIO_FILE = "Snowball Holdings.csv"

# Mapping specific categories to broader financial types
CATEGORY_TYPES = {
    # Income
    "Salary": "Income",
    "Dividends": "Income",

    # Investments
    "Investing": "Investment",

    # Fixed Expenses
    "Fixed OPEX (Mortgage)": "Fixed",
    "Rent": "Fixed",
    "Fleet Fund": "Fixed",

    # Variable Expenses
    "Living (Groceries)": "Variable",
    "Health Fund": "Variable",
    "Dining": "Variable",
    "Shopping": "Variable",

    # Default
    "Uncategorized": "Variable"
}

# Default Magic Categorization Rules
DEFAULT_RULES = [
    {'pattern': 'Trading 212', 'target': 'Investing'},
    {'pattern': 'Albert', 'target': 'Living (Groceries)'},
    {'pattern': 'Tesco', 'target': 'Living (Groceries)'},
    {'pattern': 'Hypoteka', 'target': 'Fixed OPEX (Mortgage)'},
    {'pattern': 'Shell', 'target': 'Fleet Fund'},
    {'pattern': 'Benzina', 'target': 'Fleet Fund'},
    {'pattern': 'Lekarna', 'target': 'Health Fund'},
    {'pattern': 'Dr. Max', 'target': 'Health Fund'}
]

# config/settings.py

# ... (Keep CATEGORY_TYPES as is) ...

CATEGORY_TYPES = {
    "Salary": "Income",
    "Dividends": "Income",
    "Investing": "Investment",
    "Fixed OPEX (Mortgage)": "Fixed",
    "Rent": "Fixed",
    "Fleet Fund": "Fixed",
    "Living (Groceries)": "Variable",
    "Health Fund": "Variable",
    "Dining": "Variable",
    "Shopping": "Variable",
    "Transport": "Variable",
    "Uncategorized": "Variable"
}

# GLOBAL RULES: These apply to ALL users of the system
GLOBAL_RULES = [
    {'pattern': 'Trading 212', 'target': 'Investing'},
    {'pattern': 'Hypoteka', 'target': 'Fixed OPEX (Mortgage)'},
    {'pattern': 'Shell', 'target': 'Fleet Fund'},
    {'pattern': 'Benzina', 'target': 'Fleet Fund'},
    {'pattern': 'MOL', 'target': 'Fleet Fund'},
    {'pattern': 'Lekarna', 'target': 'Health Fund'},
    {'pattern': 'Dr. Max', 'target': 'Health Fund'},
    {'pattern': 'Albert', 'target': 'Living (Groceries)'},
    {'pattern': 'Tesco', 'target': 'Living (Groceries)'},
    {'pattern': 'Lidl', 'target': 'Living (Groceries)'},
    {'pattern': 'Netflix', 'target': 'Living (Groceries)'},
    {'pattern': 'Spotify', 'target': 'Living (Groceries)'}
]