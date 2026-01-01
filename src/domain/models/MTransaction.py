from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
import streamlit as st
from src.domain.enums import TransactionType, Currency


class Transaction(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    date: date
    description: str
    amount: Decimal
    currency: Currency = Currency.CZK
    owner: UUID = Field(default_factory=lambda: UUID(st.session_state["user"]["id"]))

    # Categorization
    type: TransactionType
    category: str  # Kept as string for flexibility, or use ExpenseCategory enum

    # Banking Metadata
    source_account: Optional[str] = None
    target_account: Optional[str] = None
    batch_id: str  # Links to the import batch (e.g. "Import_20240101")

    @property
    def is_expense(self) -> bool:
        return self.amount < 0

    class Config:
        from_attributes = True