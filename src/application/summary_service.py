# src/application/summary_service.py
from decimal import Decimal
from dataclasses import dataclass
from typing import Tuple

from src.application.asset_service import AssetService
from src.application.ledger_service import LedgerService
from src.application.portfolio_service import PortfolioService


@dataclass
class ExecutiveSummary:
    net_worth: Decimal
    total_assets: Decimal
    total_liabilities: Decimal
    liquid_cash: Decimal
    invested_assets: Decimal
    monthly_income: Decimal
    monthly_spend: Decimal
    net_monthly_flow: Decimal


class SummaryService:
    def __init__(self,
                 asset_service: AssetService,
                 ledger_service: LedgerService,
                 portfolio_service: PortfolioService):
        self.asset_svc = asset_service
        self.ledger_svc = ledger_service
        self.port_svc = portfolio_service

    def get_executive_summary(self) -> ExecutiveSummary:
        # 1. Asset Data
        nw_snap = self.asset_svc.get_net_worth_snapshot()

        # 2. Portfolio Data
        _, port_metrics = self.port_svc.get_portfolio_overview()

        # 3. Ledger/Cash Data
        ledger_df = self.ledger_svc.get_recent_transactions()
        ledger_balance = Decimal(ledger_df['Amount'].sum()) if not ledger_df.empty else Decimal(0)

        # 4. Monthly Flow (Simple aggregation for MVP)
        # ideally this would be filtered by current month in the repository
        monthly_income = Decimal(0)
        monthly_spend = Decimal(0)

        if not ledger_df.empty:
            # Simple check for "recent" transactions if needed,
            # for now, we take the totals of the provided view (usually loaded as all or recent)
            monthly_income = ledger_df[ledger_df['Amount'] > 0]['Amount'].sum()
            monthly_spend = ledger_df[ledger_df['Amount'] < 0]['Amount'].sum()

        # 5. Aggregate
        # Net Worth = Hard Assets (House) + Liquid Cash (Ledger) + Investments (Portfolio) - Liabilities
        # Note: nw_snap.net_worth usually includes Assets - Liabilities.
        # If Assets doesn't track Cash/Investments, we add them here.

        real_assets = nw_snap.total_assets + ledger_balance + port_metrics.total_value
        real_net_worth = real_assets - nw_snap.total_liabilities

        return ExecutiveSummary(
            net_worth=real_assets - nw_snap.total_liabilities,
            total_assets=real_assets,
            total_liabilities=nw_snap.total_liabilities,
            liquid_cash=ledger_balance,
            invested_assets=port_metrics.total_value,
            monthly_income=monthly_income,
            monthly_spend=monthly_spend,  # expenses are usually negative
            net_monthly_flow=monthly_income + monthly_spend
        )