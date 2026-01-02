# src/domain/models/MTransaction.py

from typing import Optional, List
from uuid import UUID, uuid4
from datetime import date as dt_date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from src.domain.enums import TransactionType, Currency
from sqlalchemy import Numeric, Column, JSON


class Transaction(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: dt_date = Field(index=True)
    description: str
    amount: Decimal = Field(default=Decimal('0.00'), sa_column=Column(Numeric(20, 2)))
    currency: Currency = Field(default=Currency.CZK)
    owner: UUID = Field(index=True)

    transaction_type: TransactionType
    category: str

    source_account: Optional[str] = None
    target_account: Optional[str] = None
    batch_id: str = Field(index=True)
    notes: Optional[str] = None
    tags: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    @property
    def is_expense(self) -> bool:
        return self.amount < 0

    @property
    def account(self) -> str:
        if self.is_expense:
            return self.source_account or "Unknown"
        else:
            return self.target_account or "Unknown"
