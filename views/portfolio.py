# views/portfolio.py
import streamlit as st
from services.portfolio import PortfolioService
from components import visuals


def render_view():
    st.title("📈 Investment Portfolio")

    service = PortfolioService()
    data = service.load_data()

    snap = data['snapshot']
    hist = data['history']

    # Uploaders
    with st.expander("Update Data Sources"):
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Holdings (Current Position)")
            s_file = st.file_uploader("Upload Snapshot CSV", type='csv', key="snap_up")
            if s_file:
                service.save_file(s_file, "snapshot")
                st.rerun()
        with c2:
            st.caption("History (Transaction Log)")
            h_file = st.file_uploader("Upload History CSV", type='csv', key="hist_up")
            if h_file:
                service.save_file(h_file, "history")
                st.rerun()

    # Visualization
    if snap or hist:
        # Use the shared visual component ported from Master
        visuals.render_unified_portfolio(snap, hist)
    else:
        st.info("👋 Upload your portfolio exports (Snapshot or History) to see analytics.")