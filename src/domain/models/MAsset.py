# src/domain/models/MAsset.py

from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric
from src.domain.enums import AssetCategory, Currency, RealEstateType
from datetime import date


class Asset(SQLModel, table=True):
    __table_args__ = {'extend_existing': True}
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
    city: Optional[str] = None
    postal_code: Optional[str] = None
    property_type: Optional[RealEstateType] = None
    area_m2: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))
    annual_cost_projection: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))

    # Vehicle Fields
    brand: Optional[str] = None
    model: Optional[str] = None
    color: Optional[str] = None
    year_made: Optional[int] = None
    kilometers_driven: Optional[int] = None
    acquisition_price: Optional[Decimal] = Field(default=None, sa_type=Numeric(20, 2))
    acquisition_date: Optional[date] = None
    insurance_cost: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))

    # Cash / Banking Fields
    cash_type: Optional[str] = None
    bucket_name: Optional[str] = None  # e.g. "Vacation Fund" (Envelope)
    account_identifier: Optional[str] = None # Combined field for account number/bank code/IBAN

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = self._construct_name()

    def _construct_name(self) -> str:
        if self.category == AssetCategory.REAL_ESTATE:
            return f"{self.property_type.value if self.property_type else ''} - {self.address or ''}"
        elif self.category == AssetCategory.VEHICLE:
            return f"{self.year_made or ''} {self.brand or ''} {self.model or ''}"
        elif self.category == AssetCategory.CASH:
            return f"{self.cash_type or ''} - {self.account_identifier or ''}"
        return self.name


class NetWorthSnapshot(SQLModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    currency: Currency = Currency.CZK