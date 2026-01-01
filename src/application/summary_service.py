# src/application/summary_service.py
from decimal import Decimal
from dataclasses import dataclass
from src.application.asset_service import AssetService
from src.application.ledger_service import LedgerService
from src.application.portfolio_service import PortfolioService
from src.application.liability_service import LiabilityService

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
                 portfolio_service: PortfolioService,
                 liability_service: LiabilityService):  # <--- NEW ARG
        self.asset_svc = asset_service
        self.ledger_svc = ledger_service
        self.port_svc = portfolio_service
        self.liab_svc = liability_service

    def get_executive_summary(self) -> ExecutiveSummary:
        # 1. Assets (Real Estate, Vehicles, Cash objects)
        assets = self.asset_svc.get_user_assets()
        hard_assets_val = sum((a.value for a in assets), Decimal(0))

        # 2. Liabilities (Mortgages, Loans)
        liabilities_val = self.liab_svc.get_total_liabilities()

        # 3. Portfolio
        _, port_metrics = self.port_svc.get_portfolio_overview()

        # 4. Ledger (Operating Cash)
        ledger_df = self.ledger_svc.get_recent_transactions()
        ledger_balance = Decimal(ledger_df['Amount'].sum()) if not ledger_df.empty else Decimal(0)

        monthly_income = Decimal(0)
        monthly_spend = Decimal(0)
        if not ledger_df.empty:
            monthly_income = ledger_df[ledger_df['Amount'] > 0]['Amount'].sum()
            monthly_spend = ledger_df[ledger_df['Amount'] < 0]['Amount'].sum()

        # 5. Aggregation
        total_assets = hard_assets_val + ledger_balance + port_metrics.total_value
        net_worth = total_assets - liabilities_val

        return ExecutiveSummary(
            net_worth=net_worth,
            total_assets=total_assets,
            total_liabilities=liabilities_val,
            liquid_cash=ledger_balance,
            invested_assets=port_metrics.total_value,
            monthly_income=monthly_income,
            monthly_spend=monthly_spend,
            net_monthly_flow=monthly_income + monthly_spend
        )