from core.enums import TransactionType, ExpenseCategory, IncomeCategory

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

    "Investment Deposit": "Investment",
    "Investment Withdrawal": "Investment",

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

# Restored Global Categorization Rules
GLOBAL_RULES = [
    {'pattern': 'Trading 212', 'category': 'Investment Deposit', 'type': TransactionType.INVESTMENT},
    {'pattern': 'XTB', 'category': 'Investment Deposit', 'type': TransactionType.INVESTMENT},
    {'pattern': 'Hypoteka', 'category': ExpenseCategory.HOUSING.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Shell', 'category': ExpenseCategory.TRANSPORT.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Benzina', 'category': ExpenseCategory.TRANSPORT.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'MOL', 'category': ExpenseCategory.TRANSPORT.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Uber', 'category': ExpenseCategory.TRANSPORT.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Bolt', 'category': ExpenseCategory.TRANSPORT.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Lekarna', 'category': ExpenseCategory.HEALTH.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Dr. Max', 'category': ExpenseCategory.HEALTH.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Albert', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Tesco', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Lidl', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Kaufland', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Rohlik', 'category': ExpenseCategory.GROCERIES.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Netflix', 'category': ExpenseCategory.SUBSCRIPTIONS.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'Spotify', 'category': ExpenseCategory.SUBSCRIPTIONS.value, 'type': TransactionType.EXPENSE},
    {'pattern': 'YouTube', 'category': ExpenseCategory.SUBSCRIPTIONS.value, 'type': TransactionType.EXPENSE}
]

# UI Options
UI_CATEGORIES = {
    TransactionType.INCOME.value: [e.value for e in IncomeCategory],
    TransactionType.EXPENSE.value: [e.value for e in ExpenseCategory],
    TransactionType.INVESTMENT.value: ["Investment Deposit", "Investment Withdrawal"]
}