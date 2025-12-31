from enum import Enum, auto

class TransactionType(Enum):
    INCOME = "Income"
    EXPENSE = "Expense"
    INVESTMENT = "Investment"
    TRANSFER = "Transfer"

class ExpenseType(Enum):
    FIXED = "Fixed"
    VARIABLE = "Variable"

class ExpenseCategory(Enum):
    HOUSING = "Housing (Mortgage/Rent)"
    UTILITIES = "Utilities"
    GROCERIES = "Groceries"
    TRANSPORT = "Transport (Fuel/Taxi)"
    SHOPPING = "Shopping"
    HEALTH = "Health & Wellness"
    SUBSCRIPTIONS = "Subscriptions"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    OTHER = "Other Expense"

class IncomeCategory(Enum):
    SALARY = "Salary"
    DIVIDENDS = "Dividends"
    BUSINESS = "Business Income"
    REFUNDS = "Refunds"
    OTHER = "Other Income"

class AssetCategory(Enum):
    REAL_ESTATE = "Real Estate"
    VEHICLE = "Vehicle"
    CASH = "Cash"
    EQUITY = "Equity"

CATEGORY_METADATA = {
    ExpenseCategory.HOUSING: {"type": "Fixed", type: "Expense"},
    ExpenseCategory.UTILITIES: {"type": "Fixed"},
    ExpenseCategory.GROCERIES: {"type": "Variable"},
    ExpenseCategory.TRANSPORT: {"type": "Variable"},
    ExpenseCategory.SHOPPING: {"type": "Variable"},
    ExpenseCategory.HEALTH: {"type": "Variable"},
    ExpenseCategory.SUBSCRIPTIONS: {"type": "Variable"},
    ExpenseCategory.TRAVEL: {"type": "Variable"},
    ExpenseCategory.EDUCATION: {"type": "Variable"},
    ExpenseCategory.OTHER: {"type": "Variable"},
    IncomeCategory.SALARY: {"recurring": True},
    IncomeCategory.DIVIDENDS: {"recurring": True},
    IncomeCategory.BUSINESS: {"recurring": False},
    IncomeCategory.REFUNDS: {"recurring": False},
    IncomeCategory.OTHER: {"recurring": False},
    AssetCategory.REAL_ESTATE: {"liquidity": "Low"},
    AssetCategory.VEHICLE: {"liquidity": "Medium"},
    AssetCategory.CASH: {"liquidity": "High"},
    AssetCategory.EQUITY: {"liquidity": "Medium"}
}
