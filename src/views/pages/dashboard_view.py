import streamlit as st
from src.container import get_container

def render_view():
    st.title("📊 Executive Dashboard")

    # 1. Get Services from Container
    container = get_container()
    summary_svc = container['summary']

    # 2. Get Logic (One line!)
    data = summary_svc.get_executive_summary()

    # 3. Render
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Worth", f"{data.net_worth:,.0f} CZK")
    c2.metric("Total Assets", f"{data.total_assets:,.0f} CZK")
    c3.metric("Investments", f"{data.invested_assets:,.0f} CZK")
    c4.metric("Operating Cash", f"{data.liquid_cash:,.0f} CZK")

    st.divider()

    st.subheader("Cashflow Overview")
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Income", f"{data.monthly_income:,.0f} CZK")
    k2.metric("Total Spend", f"{data.monthly_spend:,.0f} CZK")
    k3.metric("Net Flow", f"{data.net_monthly_flow:,.0f} CZK")