from core.enums import TransactionType, ExpenseCategory, IncomeCategory, TransferCategory, InvestmentCategory

# Default Filenames
DEFAULT_PORTFOLIO_FILE = "Snowball Holdings.csv"
DEFAULT_HISTORY_FILE = "Snowball History.csv"

# Map Categories to "Fixed" vs "Variable" (Restored from your settings.py)
CATEGORY_TYPE_MAP = {
    IncomeCategory.SALARY.value: "Income",
    IncomeCategory.DIVIDENDS.value: "Income",
    IncomeCategory.BUSINESS.value: "Income",
    IncomeCategory.REFUNDS.value: "Income",
    IncomeCategory.OTHER.value: "Income",

    TransferCategory.INTERNAL.value: "Transfer",
    TransferCategory.EXCHANGE.value: "Transfer",

    ExpenseCategory.HOUSING.value: "Fixed",
    ExpenseCategory.UTILITIES.value: "Fixed",
    ExpenseCategory.SUBSCRIPTIONS.value: "Fixed",
    ExpenseCategory.EDUCATION.value: "Fixed",

    ExpenseCategory.GROCERIES.value: "Variable",
    ExpenseCategory.TRANSPORT.value: "Variable",
    ExpenseCategory.HEALTH.value: "Variable",
    ExpenseCategory.SHOPPING.value: "Variable",
    ExpenseCategory.TRAVEL.value: "Variable",
    ExpenseCategory.OTHER.value: "Variable",
    "Uncategorized": "Variable"
}

# Advanced Global Rules with Directionality
GLOBAL_RULES = [
    # --- INVESTMENTS ---
    {'pattern': 'Trading 212', 'category': 'Investment Deposit', 'type': TransactionType.INVESTMENT,
     'direction': 'negative'},
    {'pattern': 'XTB', 'category': 'Investment Deposit', 'type': TransactionType.INVESTMENT, 'direction': 'negative'},

    # --- COMPLEX PATTERNS (User Requested) ---

    # "HM": Refund if positive, Shopping if negative
    {'pattern': 'HM ', 'category': IncomeCategory.REFUNDS.value, 'type': TransactionType.INCOME,
     'direction': 'positive'},
    {'pattern': 'HM ', 'category': ExpenseCategory.SHOPPING.value, 'type': TransactionType.EXPENSE,
     'direction': 'negative'},

    # "FÚ" (Tax Office): Refund if positive, Expense if negative
    {'pattern': 'FÚ pro', 'category': IncomeCategory.REFUNDS.value, 'type': TransactionType.INCOME,
     'direction': 'positive'},
    {'pattern': 'FÚ pro', 'category': ExpenseCategory.OTHER.value, 'type': TransactionType.EXPENSE,
     'direction': 'negative'},  # Fines/Taxes

    # "Raiffeisenbank": Salary vs Fees/Travel
    {'pattern': 'Raiffeisenbank', 'category': IncomeCategory.SALARY.value, 'type': TransactionType.INCOME,
     'direction': 'positive'},
    {'pattern': 'Raiffeisenbank', 'category': ExpenseCategory.OTHER.value, 'type': TransactionType.EXPENSE,
     'direction': 'negative'},

    # --- STANDARD PATTERNS ---
    {'pattern': 'Hypoteka', 'category': ExpenseCategory.HOUSING.value, 'type': TransactionType.EXPENSE},

    # Lifestyle
    {'pattern': 'Lekarna', 'category': ExpenseCategory.HEALTH.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Dr. Max', 'category': ExpenseCategory.HEALTH.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Albert', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Tesco', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Lidl', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Kaufland', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Rohlik', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Netflix', 'category': ExpenseCategory.SUBSCRIPTIONS.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Spotify', 'category': ExpenseCategory.SUBSCRIPTIONS.value, 'type': TransactionType.EXPENSE}
]

# UI Options
UI_CATEGORIES = {
    TransactionType.INCOME.value: [e.value for e in IncomeCategory],
    TransactionType.EXPENSE.value: [e.value for e in ExpenseCategory],
    TransactionType.INVESTMENT.value: [e.value for e in InvestmentCategory],
    TransactionType.TRANSFER.value: [e.value for e in TransferCategory]
}