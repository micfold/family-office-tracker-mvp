from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import date
from typing import Optional
import streamlit as st
from uuid import UUID, uuid4


class TaxLot(BaseModel):
    """
    Tracks a specific purchase of an asset for tax purposes.
    Essential for Czech 'Time Test' (3 years).
    """
    ticker: str
    date_acquired: date
    quantity: Decimal
    acquisition_price: Decimal
    currency: str
    owner: UUID = Field(default_factory=lambda: UUID(st.session_state["user"]["id"]))

    # Status
    date_sold: Optional[date] = None
    is_tax_exempt: bool = False  # True if held > 3 years (CZ)


class TaxOptimizationResult(BaseModel):
    """
    Output for the Tax Optimization Engine.
    """
    ticker: str
    sellable_tax_free_qty: Decimal
    potential_tax_liability: Decimal
    recommendation: str  # e.g., "Wait 2 months to sell for tax exemption"