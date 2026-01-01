# views/dashboard.py
import streamlit as st
from services.ledger import LedgerService
from services.portfolio import PortfolioService
from services.assets import AssetsService  # <--- NEW
from modules import analytics
from components import visuals


def render_view():
    st.title("📊 Executive Dashboard")

    # Initialize Services
    ls = LedgerService()
    ps = PortfolioService()
    as_svc = AssetsService()  # <--- NEW

    # Load Data
    ledger = ls.load_ledger()
    port_data = ps.load_data()
    assets = as_svc.load_assets()  # <--- NEW

    # --- 1. METRICS CALCULATION (Restored from Master) ---
    # Cash: Sum of physical cash wallets + ledger balance proxy
    physical_cash = sum(assets.get("Cash", {}).values())

    # Ledger balance (Simple sum of all time, or use a specific reconciliation logic)
    ledger_balance = ledger['Amount'].sum() if not ledger.empty else 0

    # Total Liquid Cash
    total_cash = physical_cash + ledger_balance

    # Investments
    investments = 0
    if port_data['snapshot'] is not None:
        investments = port_data['snapshot']['value']
    elif port_data['history'] is not None:
        investments = port_data['history']['value_proxy']

    # Hard Assets
    real_estate = assets.get("Real Estate", 0)
    vehicles = assets.get("Vehicles", 0)
    liabilities = assets.get("Mortgage", 0)

    # Net Worth
    total_assets = total_cash + investments + real_estate + vehicles
    net_worth = total_assets - liabilities

    # --- TOP ROW METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Worth", f"{net_worth:,.0f} CZK")
    c2.metric("Total Assets", f"{total_assets:,.0f} CZK")
    c3.metric("Liquid Cash", f"{total_cash:,.0f} CZK", help="Physical + Ledger Balance")
    c4.metric("Investments", f"{investments:,.0f} CZK")

    st.divider()

    # --- 2. CASHFLOW ANALYTICS ---
    if not ledger.empty:
        st.subheader("Cashflow Performance")

        # Calculate Period Metrics
        inc, exp, net = analytics.get_net_cashflow_period(ledger)

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Income", f"{inc:,.0f} CZK")
        k2.metric("Total Spend", f"{exp:,.0f} CZK", delta_color="inverse")
        k3.metric("Net Flow", f"{net:,.0f} CZK", delta=f"{net:,.0f}")

        # Render Trend Line
        st.markdown("#### Monthly Trend")
        trend_df = analytics.get_monthly_trend(ledger)
        visuals.render_trend_line(trend_df)
    else:
        st.info("💡 No cashflow data found. Go to 'Cashflow' to upload bank statements.")