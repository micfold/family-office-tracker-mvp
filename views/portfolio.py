# views/portfolio.py
import streamlit as st
from services.portfolio import PortfolioService
import plotly.express as px


def render_view():
    st.title("📈 Investment Portfolio")

    service = PortfolioService()
    data = service.load_data()

    # Uploaders
    with st.expander("Update Data Sources"):
        c1, c2 = st.columns(2)
        with c1:
            snap = st.file_uploader("Holdings (Snapshot)", type='csv')
            if snap:
                service.save_file(snap, "snapshot")
                st.rerun()
        with c2:
            hist = st.file_uploader("History (Transactions)", type='csv')
            if hist:
                service.save_file(hist, "history")
                st.rerun()

    # Visualization
    if data['snapshot'] is not None:
        df = data['snapshot']
        st.subheader("Current Holdings")

        # Key Metrics
        if 'Current value' in df.columns:
            total_val = df['Current value'].sum()
            st.metric("Portfolio Value", f"{total_val:,.0f} CZK")

            # Simple Chart
            fig = px.pie(df, values='Current value', names='Sector', title="Allocation by Sector")
            st.plotly_chart(fig, width='stretch')

        st.dataframe(df, width='stretch')
    else:
        st.info("Please upload a holdings snapshot to see visuals.")