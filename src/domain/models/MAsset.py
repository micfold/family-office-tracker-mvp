from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
import streamlit as st
from src.domain.enums import AssetCategory, Currency


class Asset(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str  # e.g., "Property & Land", "BMW X5", "Emergency Fund"
    category: AssetCategory
    value: Decimal
    currency: Currency = Currency.CZK

    # Optional: For tracking ownership or specific location data later
    owner: UUID = Field(default_factory=lambda: UUID(st.session_state["user"]["id"]))
    description: Optional[str] = None

    class Config:
        # This allows the model to work easily with ORMs later
        from_attributes = True


class NetWorthSnapshot(BaseModel):
    """
    Represents the calculated totals for a specific point in time.
    Used for the Dashboard view.
    """
    total_assets: Decimal
    total_liabilities: Decimal
    net_worth: Decimal
    currency: Currency = Currency.CZK