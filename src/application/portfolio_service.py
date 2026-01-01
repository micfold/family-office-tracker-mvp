from typing import List, Dict, Optional, Tuple
from uuid import UUID
from decimal import Decimal
import pandas as pd
import streamlit as st

from src.domain.models.MPortfolio import InvestmentPosition, InvestmentEvent, PortfolioMetrics
from src.domain.repositories.portfolio_repository import PortfolioRepository


def _get_user_id() -> UUID:
    return UUID(st.session_state["user"]["id"])


class PortfolioService:
    def __init__(self, repo: PortfolioRepository):
        self.repo = repo

    def process_files(self, snap_file=None, hist_file=None):
        if snap_file:
            self.repo.save_snapshot_file(snap_file)
        if hist_file:
            self.repo.save_history_file(hist_file)

    def get_portfolio_overview(self) -> Tuple[List[InvestmentPosition], PortfolioMetrics]:
        uid = _get_user_id()
        positions = self.repo.get_snapshot(uid)
        history = self.repo.get_history(uid)

        # 1. Aggregates from Snapshot
        total_val = sum((p.market_value for p in positions), Decimal(0))
        total_cost_snap = sum((p.cost_basis for p in positions), Decimal(0))
        proj_divs = sum((p.projected_annual_income for p in positions), Decimal(0))

        # 2. Aggregates from History
        realized_divs = Decimal(0)
        invested_cap_hist = Decimal(0)  # Calculated from buy/sell flows if snapshot cost is missing

        # Simple History Sums
        for evt in history:
            et = evt.event_type.upper()
            if 'DIV' in et:
                realized_divs += evt.total_amount
            elif 'BUY' in et or 'DEPOSIT' in et:
                invested_cap_hist += evt.total_amount
            elif 'SELL' in et or 'WITHDRAW' in et:
                # Simplified: assuming total_amount is proceeds
                # Ideally we need match logic, but for MVP:
                invested_cap_hist -= evt.total_amount

                # 3. Strategy: Prefer Snapshot Cost, Fallback to History Flow
        final_cost = total_cost_snap if total_cost_snap > 0 else invested_cap_hist
        if final_cost < 0: final_cost = Decimal(0)

        metrics = PortfolioMetrics(
            total_value=total_val,
            total_invested=final_cost,
            total_profit=total_val - final_cost,
            total_profit_pct=((total_val - final_cost) / final_cost * 100) if final_cost > 0 else 0,
            realized_dividends_all_time=realized_divs,
            projected_annual_dividends=proj_divs,
            yield_on_cost=(proj_divs / final_cost * 100) if final_cost > 0 else 0
        )

        return positions, metrics

    def get_invested_capital_curve(self) -> pd.DataFrame:
        """Recreates the 'Invested Capital' area chart logic."""
        history = self.repo.get_history(_get_user_id())
        if not history: return pd.DataFrame()

        # Convert to DF for easier time-series manipulation
        data = []
        cumulative = Decimal(0)

        # Sort by date
        sorted_hist = sorted(history, key=lambda x: x.date)

        for evt in sorted_hist:
            et = evt.event_type.upper()
            if 'BUY' in et:
                cumulative += evt.total_amount
            elif 'SELL' in et:
                # Heuristic: subtract proceeds from invested capital (simplified)
                # A real CFO tool would subtract only the COST BASIS of the sold portion.
                # For MVP legacy parity:
                cumulative -= evt.total_amount

            if cumulative < 0: cumulative = Decimal(0)

            data.append({"Date": evt.date, "Invested Capital": float(cumulative)})

        if not data: return pd.DataFrame()

        return pd.DataFrame(data).drop_duplicates('Date', keep='last')

    def get_dividend_history(self) -> pd.DataFrame:
        history = self.repo.get_history(_get_user_id())
        data = []
        for evt in history:
            if 'DIV' in evt.event_type.upper():
                data.append({
                    "Year": evt.date.year,
                    "Amount": float(evt.total_amount)
                })

        if not data: return pd.DataFrame()
        df = pd.DataFrame(data)
        return df.groupby('Year')['Amount'].sum().reset_index()