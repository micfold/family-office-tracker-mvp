# src/domain/models/MTransaction.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from src.domain.enums import TransactionType, Currency


class Transaction(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: date = Field(index=True)  # Indexed for sorting/filtering by date
    description: str
    amount: Decimal = Field(default=0, max_digits=20, decimal_places=2)
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
