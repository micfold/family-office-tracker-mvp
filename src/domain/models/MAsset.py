# src/domain/models/MAsset.py
from datetime import date as dt_date
from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric
from src.domain.enums import AssetCategory, Currency


class Asset(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    category: AssetCategory

    # Value is Current Market Value (or remaining debt for liabilities)
    value: Decimal = Field(default=0, sa_type=Numeric(20, 2))
    currency: Currency = Field(default=Currency.CZK)
    owner: UUID = Field(index=True)
    description: Optional[str] = None

    # --- Extended Fields (Optional based on Category) ---

    # Real Estate Fields
    address: Optional[str] = None
    area_m2: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))
    purchase_price: Optional[Decimal] = Field(default=None, sa_type=Numeric(20, 2))
    purchase_currency: Optional[Currency] = None

    # Vehicle Fields
    brand: Optional[str] = None
    model: Optional[str] = None
    insurance_cost: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))

    # Cash / Banking Fields
    cash_type: Optional[str] = None
    bucket_name: Optional[str] = None  # e.g. "Vacation Fund" (Envelope)
    account_number: Optional[str] = None
    bank_code: Optional[str] = None
    iban: Optional[str] = None

class NetWorthSnapshot(SQLModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    currency: Currency = Currency.CZK