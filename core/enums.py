from enum import Enum, auto


class TransactionType(Enum):
    INCOME = "Income"
    EXPENSE = "Expense"
    INVESTMENT = "Investment"
    TRANSFER = "Transfer"


class ExpenseType(Enum):
    FIXED = "Fixed"
    VARIABLE = "Variable"

class InvestmentCategory(Enum):
    DEPOSIT = "Investment Deposit"
    WITHDRAWAL = "Investment Withdrawal"

class TransferCategory(Enum):
    INTERNAL = "Internal Transfer"
    EXCHANGE = "Currency Exchange"


class ExpenseCategory(Enum):
    HOUSING = "Housing (Mortgage/Rent)"
    UTILITIES = "Utilities"
    GROCERIES = "Groceries"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    HEALTH = "Health & Wellness"
    SUBSCRIPTIONS = "Subscriptions"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    OTHER = "Other Expense"

class TransportSubcategory(Enum):
    FUEL = "Fuel"
    PARKING = "Parking"
    TOLLS = "Tolls"
    LEASE = "Lease"
    PUBLIC_TRANSPORT = "Public Transport"
    RIDE_SHARING = "Ride Sharing"
    MAINTENANCE = "Maintenance"
    INSURANCE = "Insurance"
    ACQUISITION = "Acquisition"


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
