# src/domain/models/MLiability.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric
from src.domain.enums import LiabilityCategory, Currency


class Liability(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str

    # Value is always positive (the amount you owe)
    amount: Decimal = Field(default=0, sa_type=Numeric(20, 2))
    currency: Currency = Field(default=Currency.CZK)
    owner: UUID = Field(index=True)

    # Specific Liability Fields
    liability_type: LiabilityCategory
    institution: Optional[str] = None
    interest_rate: Optional[Decimal] = Field(default=None, sa_type=Numeric(5, 2))
    monthly_payment_day: Optional[int] = None
    repayment_end_date: Optional[date] = None

    # Credit Card specifics
    interest_free_days: Optional[int] = None