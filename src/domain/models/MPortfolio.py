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
    sector: Optional[str] = None

    # Valuation
    current_price: Decimal
    cost_basis: Decimal  # Total Cost (or Avg Price * Qty)
    market_value: Decimal  # Current Value
    gain_loss: Decimal  # Value - Cost

    # Income
    dividend_yield_projected: Decimal = Decimal(0)  # Percentage
    projected_annual_income: Decimal = Decimal(0)

    currency: Currency = Currency.CZK


class InvestmentEvent(BaseModel):
    """Represents a Buy/Sell/Dividend event (History)."""
    id: UUID = Field(default_factory=uuid4)
    date: datetime
    ticker: str
    event_type: str  # "BUY", "SELL", "DIVIDEND"
    quantity: Optional[Decimal] = None
    price_per_share: Optional[Decimal] = None
    total_amount: Decimal  # The actual cash impact (Cost for Buy, Proceeds for Sell)
    currency: Currency
    fee: Decimal = Decimal(0)
    owner: UUID = Field(default_factory=lambda: UUID(st.session_state["user"]["id"]))


class PortfolioMetrics(BaseModel):
    """Aggregated KPIs for the dashboard."""
    total_value: Decimal = Decimal(0)
    total_invested: Decimal = Decimal(0)
    total_profit: Decimal = Decimal(0)
    total_profit_pct: Decimal = Decimal(0)

    # Dividend specifics
    realized_dividends_all_time: Decimal = Decimal(0)
    projected_annual_dividends: Decimal = Decimal(0)
    yield_on_cost: Decimal = Decimal(0)