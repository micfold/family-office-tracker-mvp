# src/domain/models/MAsset.py
from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from sqlmodel import SQLModel, Field
from src.domain.enums import AssetCategory, Currency

class Asset(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    category: AssetCategory
    # SQLModel stores Decimal as numeric; ensuring correct scale in Postgres later
    value: Decimal = Field(default=0, max_digits=20, decimal_places=2)
    currency: Currency = Field(default=Currency.CZK)
    owner: UUID = Field(index=True) # Indexed for faster "get_user_assets" queries
    description: Optional[str] = None

# NetWorthSnapshot is NOT a table, it's just a UI Data Class, so it stays Pydantic (or SQLModel without table=True)
class NetWorthSnapshot(SQLModel):
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    currency: Currency = Currency.CZK