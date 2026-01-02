# src/domain/models/MTax.py
from typing import Optional
from uuid import UUID, uuid4
from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric


class TaxLot(SQLModel, table=True):
    """
    Tracks a specific purchase of an asset for tax purposes.
    Essential for Czech 'Time Test' (3 years).
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticker: str = Field(index=True)
    date_acquired: date = Field(index=True)

    quantity: Decimal = Field(sa_type=Numeric(20, 6))
    acquisition_price: Decimal = Field(sa_type=Numeric(20, 4))
    currency: str

    owner: UUID = Field(index=True)

    # Status
    date_sold: Optional[date] = None
    is_tax_exempt: bool = Field(default=False)