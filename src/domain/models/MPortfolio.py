from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from src.domain.enums import Currency
import streamlit as st


class InvestmentPosition(BaseModel):
    """Represents a current holding (Snapshot)."""
    id: UUID = Field(default_factory=uuid4)
    ticker: str  # e.g., "VWCE"
    name: str  # e.g., "Vanguard FTSE All-World"
    quantity: Decimal
    owner: UUID = Field(default_factory=lambda: UUID(st.session_state["user"]["id"]))

    # Valuation
    current_price: Decimal
    cost_basis: Decimal  # Average buy price
    currency: Currency

    # Derived metrics (can be calculated properties or stored)
    current_value_local: Decimal
    current_value_czk: Decimal  # Normalized value


class InvestmentEvent(BaseModel):
    """Represents a Buy/Sell/Dividend event (History)."""
    id: UUID = Field(default_factory=uuid4)
    date: datetime
    ticker: str
    event_type: str  # "BUY", "SELL", "DIVIDEND"
    quantity: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    total_amount: Decimal  # The actual cash impact
    currency: Currency
    fee: Decimal = Decimal(0)
    owner: UUID = Field(default_factory=lambda: UUID(st.session_state["user"]["id"]))
