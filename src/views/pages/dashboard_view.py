import streamlit as st
from decimal import Decimal

# Import Services
from src.application.asset_service import AssetService
from src.application.ledger_service import LedgerService
from src.application.portfolio_service import PortfolioService

# Import Repos (Construction)
from src.core.json_impl import JsonAssetRepository
from src.domain.repositories.sql_repository import SqlTransactionRepository
led_svc = LedgerService(SqlTransactionRepository())

from src.domain.repositories.sql_repository import SqlPortfolioRepository
port_svc = PortfolioService(SqlPortfolioRepository())


def render_view():
    st.title("📊 Executive Dashboard")

    # 1. Initialize Services
    # In a full framework, this dependency injection is handled automatically
    as_svc = AssetService(JsonAssetRepository())
    led_svc = LedgerService(SqlTransactionRepository())
    port_svc = PortfolioService(SqlPortfolioRepository())

    # 2. Fetch Data
    # A. Net Worth Components
    nw_snap = as_svc.get_net_worth_snapshot()

    # B. Portfolio Components
    _, port_metrics = port_svc.get_portfolio_overview()

    # C. Cash/Ledger Components
    # We need the sum of the ledger for "Liquid Cash"
    # The Ledger Service returns a DF, we sum it here or add a method to service
    ledger_df = led_svc.get_recent_transactions()
    ledger_balance = Decimal(ledger_df['Amount'].sum()) if not ledger_df.empty else Decimal(0)

    # 3. Aggregate Calculations
    # Total Cash = Physical Cash (Assets) + Operating Cash (Ledger)
    # Note: AssetService.get_net_worth_snapshot() includes "Physical Cash" in total_assets
    # We should likely extract it if we want to display it separately,
    # but for High Level NW, adding Ledger Balance to the Asset Snapshot is correct.

    real_net_worth = nw_snap.net_worth + ledger_balance + port_metrics.total_value
    total_assets_combined = nw_snap.total_assets + ledger_balance + port_metrics.total_value

    # 4. Display High Level Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Worth", f"{real_net_worth:,.0f} CZK")
    c2.metric("Total Assets", f"{total_assets_combined:,.0f} CZK")
    c3.metric("Investments", f"{port_metrics.total_value:,.0f} CZK")
    c4.metric("Operating Cash", f"{ledger_balance:,.0f} CZK")

    st.divider()

    # 5. Cashflow Summary (From Ledger)
    if not ledger_df.empty:
        st.subheader("Cashflow (Last 30 Days)")
        # Simple analytics here or move to Service
        # For now, just show the totals from the whole ledger for MVP
        income = ledger_df[ledger_df['Amount'] > 0]['Amount'].sum()
        expenses = ledger_df[ledger_df['Amount'] < 0]['Amount'].sum()

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Income", f"{income:,.0f} CZK")
        k2.metric("Total Spend", f"{expenses:,.0f} CZK")
        k3.metric("Net Flow", f"{income + expenses:,.0f} CZK")
    else:
        st.info("No Cashflow data.")