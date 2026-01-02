# src/views/pages/cashflow_view.py
import streamlit as st
from src.container import get_container
from src.views.components.charts import render_spending_trend
from src.views.components.cashflow_entry_upload import render_entry_upload_tab
from src.views.components.cashflow_ledger_display import render_ledger_display


def render_view():
    st.title("💸 Cashflow & Ledger")

    container = get_container()
    service = container['ledger']
    ledger_df = service.get_recent_transactions()

    tabs = st.tabs(["📊 Analytics", "📥 Entry & Upload", "📜 Ledger Data", "📂 Batch Management"])

    with tabs[0]:
        st.subheader("Cashflow Trends")
        render_spending_trend(ledger_df)

    with tabs[1]:
        render_entry_upload_tab(service)

    with tabs[2]:
        render_ledger_display(ledger_df, service, key_suffix="ledger")

    with tabs[3]:
        # Keep Batch Management in ledger display component to reduce duplication
        render_ledger_display(ledger_df, service, key_suffix="batch")
