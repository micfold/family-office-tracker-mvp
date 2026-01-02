# src/domain/models/MLiability.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from src.domain.enums import LiabilityCategory, Currency
from sqlalchemy import Numeric


class Liability(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str

    # Value is always positive (the amount you owe)
    amount: Decimal = Field(default=0, sa_type=Numeric(20, 2))
    currency: Currency = Field(default=Currency.CZK)
    owner: UUID = Field(index=True)

    # Link to an Asset (e.g. Mortgage -> House)
    # ondelete="SET NULL" ensures if Asset is deleted, Liability remains but unlinked
    asset_id: Optional[UUID] = Field(default=None, foreign_key="asset.id")

    # Specific Liability Fields
    liability_type: LiabilityCategory
    institution: str
    interest_rate: Decimal = Field(default=0, sa_type=Numeric(5, 2))
    has_insurance: bool = False
    insurance_cost: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))

    # --- Mortgage-Specific Fields ---
    start_date: Optional[date] = None
    annual_interest_paid: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self._construct_name()

    def _construct_name(self) -> str:
        return f"{self.institution or ''} - {self.liability_type.value if self.liability_type else ''}"
