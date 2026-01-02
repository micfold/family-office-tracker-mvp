# src/views/pages/portfolio_view.py
import streamlit as st
import plotly.express as px
from src.container import get_container
from src.views.components.charts import render_portfolio_allocation, render_invested_capital_curve


# Note: We don't import Service or Domain Models anymore!

def render_view():
    st.title("📈 Investment Portfolio")

    # 1. Get ViewModel
    container = get_container()
    vm = container['portfolio_vm']  # We will add this to container next

    # 2. Uploaders (Action)
    with st.expander("Update Data Sources"):
        c1, c2 = st.columns(2)
        s_file = c1.file_uploader("Upload Snapshot CSV", type='csv', key="snap_up")
        h_file = c2.file_uploader("Upload History CSV", type='csv', key="hist_up")

        if (s_file or h_file) and st.button("Process & Save"):
            if vm.process_uploads(s_file, h_file):
                st.success("Data Updated!")
                st.rerun()

    # 3. Main Display (Passive)
    metrics = vm.get_metrics()

    # KPI Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", metrics.total_value)
    m2.metric("Total Profit", metrics.total_profit, metrics.total_profit_pct, delta_color=metrics.total_profit_color)
    m3.metric("Invested Capital", metrics.invested_capital)
    m4.metric("Divs (All Time)", metrics.dividends_all_time)

    st.divider()

    # Charts
    c1, c2 = st.columns(2)
    with c1:
        # Note: Chart component might need slight adjustment if it expects raw objects
        # For now, we pass what the VM provides
        render_portfolio_allocation(vm.get_allocation_chart_data())
    with c2:
        render_invested_capital_curve(vm.get_curve_data())

    # Dividend Intelligence
    st.subheader("Dividend Intelligence")
    div_cols = st.columns(2)
    with div_cols[0]:
        st.caption("Annual Dividend Income")
        div_df = vm.get_dividend_data()
        if not div_df.empty:
            st.plotly_chart(px.bar(div_df, x='Year', y='Amount'), use_container_width=True)

    with div_cols[1]:
        st.metric("Projected Annual Income", metrics.proj_annual_income)
        st.metric("Yield on Cost", metrics.yield_on_cost)

    # Grid
    st.subheader("Holdings")
    df = vm.get_holdings_grid()
    if not df.empty:
        st.dataframe(df, use_container_width=True)