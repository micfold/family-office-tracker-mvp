# src/views/models/portfolio_vm.py
import pandas as pd
from dataclasses import dataclass
from src.application.portfolio_service import PortfolioService


@dataclass
class PortfolioDisplayMetrics:
    total_value: str
    total_profit: str
    total_profit_pct: str
    total_profit_color: str  # "normal" or "inverse"
    invested_capital: str
    dividends_all_time: str
    proj_annual_income: str
    yield_on_cost: str


class PortfolioViewModel:
    def __init__(self, service: PortfolioService):
        self.svc = service

    def process_uploads(self, snap_file, hist_file) -> bool:
        """Returns True if processing happened."""
        if snap_file or hist_file:
            self.svc.process_files(snap_file, hist_file)
            return True
        return False

    def get_metrics(self) -> PortfolioDisplayMetrics:
        _, metrics = self.svc.get_portfolio_overview()

        # Logic for formatting and colors happens HERE, not in the View
        is_profit = metrics.total_profit >= 0

        return PortfolioDisplayMetrics(
            total_value=f"{metrics.total_value:,.0f} CZK",
            total_profit=f"{metrics.total_profit:,.0f} CZK",
            total_profit_pct=f"{metrics.total_profit_pct:.1f}%",
            total_profit_color="normal" if is_profit else "inverse",
            invested_capital=f"{metrics.total_invested:,.0f} CZK",
            dividends_all_time=f"{metrics.realized_dividends_all_time:,.0f} CZK",
            proj_annual_income=f"{metrics.projected_annual_dividends:,.0f} CZK",
            yield_on_cost=f"{metrics.yield_on_cost:.2f}%"
        )

    def get_holdings_grid(self) -> pd.DataFrame:
        positions, _ = self.svc.get_portfolio_overview()
        if not positions:
            return pd.DataFrame()

        # Transform Domain Objects to simple Dicts for the DataGrid
        data = [{
            "Ticker": p.ticker,
            "Name": p.name,
            "Sector": p.sector,
            "Qty": float(p.quantity),
            "Price": float(p.current_price),
            "Value": float(p.market_value),
            "Gain/Loss": float(p.gain_loss),
            "YOC %": float(p.dividend_yield_projected)  # Simplified for MVP
        } for p in positions]

        return pd.DataFrame(data)

    def get_allocation_chart_data(self):
        positions, _ = self.svc.get_portfolio_overview()
        return positions  # Passing objects to chart is okay, or transform here

    def get_curve_data(self) -> pd.DataFrame:
        return self.svc.get_invested_capital_curve()

    def get_dividend_data(self) -> pd.DataFrame:
        return self.svc.get_dividend_history()