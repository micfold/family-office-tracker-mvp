# src/views/components/kpi_cards.py
import streamlit as st
from src.application.summary_service import ExecutiveSummary


def render_executive_summary_cards(data: ExecutiveSummary):
    """
    Renders the top-level 4-column summary used in Dashboard and Assets views.
    """
    c1, c2, c3, c4 = st.columns(4)

    # You can easily change the styling for the whole app here
    c1.metric("Net Worth", f"{data.net_worth:,.0f} CZK", help="Assets - Liabilities")
    c2.metric("Total Assets", f"{data.total_assets:,.0f} CZK")
    c3.metric("Investments", f"{data.invested_assets:,.0f} CZK")
    c4.metric("Operating Cash", f"{data.liquid_cash:,.0f} CZK")

    st.divider()


def render_cashflow_summary(data: ExecutiveSummary):
    """
    Renders the Cashflow high-level metrics.
    """
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Income (Mo)", f"{data.monthly_income:,.0f} CZK")
    k2.metric("Total Spend (Mo)", f"{data.monthly_spend:,.0f} CZK")
    k3.metric("Net Flow (Mo)", f"{data.net_monthly_flow:,.0f} CZK",
              delta_color="normal" if data.net_monthly_flow > 0 else "inverse")