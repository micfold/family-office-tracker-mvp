import streamlit as st
import plotly.express as px
from src.container import get_container
from src.views.components.charts import render_portfolio_allocation, render_invested_capital_curve

def render_view():
    st.title("📈 Investment Portfolio")

    container = get_container()
    service = container['portfolio']

    # 1. Uploaders
    with st.expander("Update Data Sources"):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Holdings (Current Position)")
            s_file = st.file_uploader("Upload Snapshot CSV", type='csv', key="snap_up")
        with c2:
            st.caption("History (Transaction Log)")
            h_file = st.file_uploader("Upload History CSV", type='csv', key="hist_up")

        if s_file or h_file:
            if st.button("Process & Save"):
                service.process_files(s_file, h_file)
                st.success("Data Updated!")
                st.rerun()

    # 2. Main Logic
    positions, metrics = service.get_portfolio_overview()

    if not positions and metrics.total_invested == 0:
        st.info("👋 Upload your portfolio exports to see analytics.")
        return

    # 3. KPI Header
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Portfolio Value", f"{metrics.total_value:,.0f} CZK")
    m2.metric("Total Profit", f"{metrics.total_profit:,.0f} CZK", delta=f"{metrics.total_profit_pct:.1f}%")
    m3.metric("Invested Capital", f"{metrics.total_invested:,.0f} CZK")
    m4.metric("Divs (All Time)", f"{metrics.realized_dividends_all_time:,.0f} CZK")

    st.divider()

    # 4. Visuals (Top Row)
    c1, c2 = st.columns(2)
    with c1:
        render_portfolio_allocation(positions)
    with c2:
        curve_df = service.get_invested_capital_curve()
        render_invested_capital_curve(curve_df)

    # 5. Dividend Intelligence
    st.subheader("Dividend Intelligence")
    div_cols = st.columns(2)
    with div_cols[0]:
        st.caption("Annual Dividend Income")
        div_df = service.get_dividend_history()
        if not div_df.empty:
            st.plotly_chart(px.bar(div_df, x='Year', y='Amount'), use_container_width=True)

    with div_cols[1]:
        st.metric("Projected Annual Income", f"{metrics.projected_annual_dividends:,.0f} CZK")
        st.metric("Yield on Cost", f"{metrics.yield_on_cost:.2f}%")

    # 6. Data Grid
    st.subheader("Holdings")
    if positions:
        # Convert objects to simple dicts for dataframe display
        grid_data = [{
            "Ticker": p.ticker,
            "Name": p.name,
            "Qty": float(p.quantity),
            "Value": float(p.market_value),
            "Profit": float(p.gain_loss),
            "Yield": float(p.dividend_yield_projected)
        } for p in positions]
        st.dataframe(grid_data, use_container_width=True)