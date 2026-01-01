# views/dashboard.py
import streamlit as st
from services.ledger import LedgerService
from services.portfolio import PortfolioService
from modules import analytics
from components import visuals


def render_view():
    st.title("📊 Executive Dashboard")

    # Initialize Services
    ls = LedgerService()
    ps = PortfolioService()

    # Load Data
    ledger = ls.load_ledger()
    port_data = ps.load_data()

    # Calculate Metrics
    # 1. Net Worth (Simplified)
    cash = 0
    if not ledger.empty:
        # Assuming running balance calculation or manual input
        cash = ledger['Amount'].sum()

    investments = 0
    if port_data['snapshot'] is not None:
        investments = port_data['snapshot']['value']
    elif port_data['history'] is not None:
        investments = port_data['history']['value_proxy']

    total_assets = cash + investments

    # Top Row Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Liquid Assets", f"{total_assets:,.0f} CZK")
    c2.metric("Cash Position", f"{cash:,.0f} CZK", help="Sum of all ledger transactions")
    c3.metric("Investment Portfolio", f"{investments:,.0f} CZK")

    # 2. CASHFLOW ANALYTICS (Restored from Master)
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

        # Recent Activity
        st.divider()
        st.subheader("Recent Activity")
        st.dataframe(ledger.sort_values('Date', ascending=False).head(5), width='stretch')
    else:
        st.info("💡 No cashflow data found. Go to 'Cashflow' to upload bank statements.")