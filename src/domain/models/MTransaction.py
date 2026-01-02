# src/domain/models/MTransaction.py

from typing import Optional
from uuid import UUID, uuid4
from datetime import date as dt_date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from src.domain.enums import TransactionType, Currency
from sqlalchemy import Numeric, Column


class Transaction(SQLModel, table=True):
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
    batch_id: str = Field(index=True)  # Indexed for "Delete Batch"

    @property
    def is_expense(self) -> bool:
        return self.amount < 0
