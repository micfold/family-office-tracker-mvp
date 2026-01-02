# src/domain/models/MPortfolio.py
from uuid import UUID, uuid4
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Numeric
from src.domain.enums import Currency


class InvestmentPosition(SQLModel, table=True):
    """Snapshot of current holdings."""
    __table_args__ = {'extend_existing': True}
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ticker: str = Field(index=True)
    name: str

    # All decimals must use sa_type=Numeric(precision, scale)
    quantity: Decimal = Field(sa_type=Numeric(20, 6))
    owner: UUID = Field(index=True)
    sector: Optional[str] = None

    current_price: Decimal = Field(sa_type=Numeric(20, 4))
    cost_basis: Decimal = Field(sa_type=Numeric(20, 2))
    market_value: Decimal = Field(sa_type=Numeric(20, 2))
    gain_loss: Decimal = Field(sa_type=Numeric(20, 2))

    dividend_yield_projected: Decimal = Field(default=0, sa_type=Numeric(10, 4))
    projected_annual_income: Decimal = Field(default=0, sa_type=Numeric(20, 2))
    currency: Currency = Field(default=Currency.CZK)


class InvestmentEvent(SQLModel, table=True):
    """History log (Buy/Sell/Div)."""
    __table_args__ = {'extend_existing': True}
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    date: datetime = Field(index=True)
    ticker: str = Field(index=True)
    event_type: str

    quantity: Optional[Decimal] = Field(default=None, sa_type=Numeric(20, 6))
    price_per_share: Optional[Decimal] = Field(default=None, sa_type=Numeric(20, 4))

    total_amount: Decimal = Field(sa_type=Numeric(20, 2))
    currency: Currency
    fee: Decimal = Field(default=0, sa_type=Numeric(10, 2))
    owner: UUID = Field(index=True)


# Metrics stays as a data container (not a table), so standard Pydantic defaults are fine
class PortfolioMetrics(SQLModel):
    total_value: Decimal = 0
    total_invested: Decimal = 0
    total_profit: Decimal = 0
    total_profit_pct: Decimal = 0
    realized_dividends_all_time: Decimal = 0
    projected_annual_dividends: Decimal = 0
    yield_on_cost: Decimal = 0