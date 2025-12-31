# views/dashboard.py
import streamlit as st
from services.ledger import LedgerService
from services.portfolio import PortfolioService


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
        if 'Current value' in port_data['snapshot'].columns:
            investments = port_data['snapshot']['Current value'].sum()

    total_assets = cash + investments

    # Display
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Liquid Assets", f"{total_assets:,.0f} CZK")
    c2.metric("Cash Position", f"{cash:,.0f} CZK")
    c3.metric("Investment Portfolio", f"{investments:,.0f} CZK")

    st.divider()
    st.subheader("Recent Activity")
    if not ledger.empty:
        st.dataframe(ledger.sort_values('Date', ascending=False).head(5), width='stretch')
    else:
        st.info("No transaction data found. Go to 'Cashflow' to upload.")