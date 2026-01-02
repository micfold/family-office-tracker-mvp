# src/application/portfolio_service.py
from typing import List, Tuple
from uuid import UUID
from decimal import Decimal
import pandas as pd
import streamlit as st

# Updated Import: Added parse_portfolio_history
from src.core.parsers import parse_portfolio_snapshot, parse_portfolio_history
from src.domain.models.MPortfolio import InvestmentPosition, InvestmentEvent, PortfolioMetrics
from src.domain.repositories.portfolio_repository import PortfolioRepository

def _get_user_id() -> UUID:
    return UUID(st.session_state["user"]["id"])

class PortfolioService:
    def __init__(self, repo: PortfolioRepository):
        self.repo = repo

    def process_files(self, snap_file=None, hist_file=None):
        uid = _get_user_id()

        # 1. Snapshot -> Parse -> Save to DB
        if snap_file:
            positions = parse_portfolio_snapshot(snap_file, uid)
            if positions:
                self.repo.save_positions(positions)

        # 2. History -> Parse -> Save to DB
        if hist_file:
            events = parse_portfolio_history(hist_file, uid)
            if events:
                self.repo.save_events(events)

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
        invested_cap_hist = Decimal(0)

        # Simple History Sums
        for evt in history:
            et = evt.event_type.upper()
            amt = abs(evt.total_amount)
            if 'DIV' in et:
                realized_divs += amt
            elif 'BUY' in et or 'DEPOSIT' in et:
                invested_cap_hist += amt
            elif 'SELL' in et or 'WITHDRAW' in et:
                invested_cap_hist -= amt

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

        data = []
        cumulative = Decimal(0)
        sorted_hist = sorted(history, key=lambda x: x.date)

        for evt in sorted_hist:
            et = evt.event_type.upper()
            amt = abs(evt.total_amount)
            if 'BUY' in et or 'DEPOSIT' in et:
                cumulative += amt
            elif 'SELL' in et or 'WITHDRAW' in et:
                cumulative -= amt

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