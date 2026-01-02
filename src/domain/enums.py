from enum import Enum, auto

class Currency(str, Enum):
    CZK = "CZK"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class CashCategory(str, Enum):
    CHECKING_ACCOUNT = "Checking Account"
    SAVINGS_ACCOUNT = "Savings Account"
    CASH_ON_HAND = "Cash on Hand"
    OTHER = "Other Cash Category"


class AssetCategory(str, Enum):
    REAL_ESTATE = "Real Estate"
    VEHICLE = "Vehicle"
    CASH = "Cash"
    EQUITY = "Equity"

class LiabilityCategory(str, Enum):
    MORTGAGE = "Mortgage"
    PERSONAL_LOAN = "Personal Loan"
    CREDIT_CARD = "Credit Card"
    OTHER = "Other Liability"


class TransactionType(str, Enum):
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
    HOUSING = "Housing"
    TRANSPORTATION = "Transportation"
    FOOD = "Food"
    UTILITIES = "Utilities"
    INSURANCE = "Insurance"
    HEALTHCARE = "Healthcare"
    SAVINGS = "Savings & Investments"
    PERSONAL_SPENDING = "Personal Spending"
    GROCERIES = "Groceries"
    TRANSPORT = "Transport"
    SHOPPING = "Shopping"
    HEALTH = "Health"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    OTHER = "Other"
    ENTERTAINMENT = "Entertainment"
    SUBSCRIPTIONS = "Subscriptions"
    MISCELLANEOUS = "Miscellaneous"


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

class RealEstateType(str, Enum):
    PRIMARY_RESIDENCE = "Primary Residence"
    SECONDARY_RESIDENCE = "Secondary Residence"
    VACATION_HOME = "Vacation Home"
    INVESTMENT_PROPERTY = "Investment Property"
    LAND = "Land"
    OTHER = "Other"

CATEGORY_METADATA = {
    # Expense Categories mapped to Expense Types and Transaction Classes
    ExpenseCategory.HOUSING.value: {"type": "Fixed", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.UTILITIES.value: {"type": "Fixed", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.SUBSCRIPTIONS.value: {"type": "Fixed", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.GROCERIES.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.TRANSPORT.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.SHOPPING.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.HEALTH.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.TRAVEL.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.EDUCATION.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},
    ExpenseCategory.OTHER.value: {"type": "Variable", "class": TransactionType.EXPENSE.value},

    # Transport Subcategories mapped to Transport Expense Category
    TransportSubcategory.FUEL.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.PARKING.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.TOLLS.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.LEASE.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.PUBLIC_TRANSPORT.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.RIDE_SHARING.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.MAINTENANCE.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.INSURANCE.value: {"class": ExpenseCategory.TRANSPORT.value},
    TransportSubcategory.ACQUISITION.value: {"class": ExpenseCategory.TRANSPORT.value}
}
