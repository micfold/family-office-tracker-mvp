import streamlit as st
import pandas as pd
from datetime import date
from src.container import get_container
from src.domain.enums import CATEGORY_METADATA
from src.views.components.charts import render_spending_trend
from config import UI_CATEGORIES


def render_entry_upload_tab(service):
    c1, c2 = st.columns(2)

    # Manual Entry
    with c1:
        st.subheader("Manual Entry")
        with st.form("manual_add"):
            d = st.date_input("Date", date.today())
            desc = st.text_input("Description")
            amt = st.number_input("Amount", step=100.0)

            # Safe retrieval of keys
            type_options = list(UI_CATEGORIES.keys())
            t_type = st.selectbox("Type", type_options)

            # Helper to get categories safely
            cat_options = UI_CATEGORIES.get(t_type, {}).get('class', ["Uncategorized"])
            if isinstance(cat_options, str):
                cat_options = [cat_options]

            cat = st.selectbox("Category", cat_options)

            if st.form_submit_button("Add Transaction"):
                service.add_manual_transaction({
                    'date': d,
                    'description': desc,
                    'amount': amt,
                    'category': cat,
                    'transaction_type': t_type,
                    'batch_id': 'Manual'
                })
                st.success("Added!")
                st.rerun()

    # Batch Upload
    with c2:
        st.subheader("Batch Upload")
        files = st.file_uploader("Bank CSVs/ZIPs", accept_multiple_files=True)
        if files and st.button("Process Files"):
            with st.spinner("Processing..."):
                count, _ = service.process_uploads(files)
                st.success(f"Processed {count} transactions.")
                st.rerun()


def render_view():
    st.title("💸 Cashflow & Ledger")

    # Dependency Injection
    container = get_container()
    service = container['ledger']

    # Load Data
    ledger_df = service.get_recent_transactions()

    tabs = st.tabs(["📊 Analytics", "📥 Entry & Upload", "📜 Ledger Data", "📂 Batch Management"])

    # --- TAB 1: ANALYTICS ---
    with tabs[0]:
        st.subheader("Cashflow Trends")
        render_spending_trend(ledger_df)

    # --- TAB 2: ENTRY ---
    with tabs[1]:
        render_entry_upload_tab(service)

    # --- TAB 3: DATA ---
    with tabs[2]:
        if not ledger_df.empty:
            st.dataframe(ledger_df.sort_values('Date', ascending=False), use_container_width=True)
        else:
            st.info("No data found.")

    # --- TAB 4: BATCHES ---
    with tabs[3]:
        history = service.get_batch_history()
        if not history.empty:
            st.dataframe(history, use_container_width=True)
            sel = st.selectbox("Select Batch", history['Batch_ID'].unique())
            if st.button("Delete Batch"):
                service.delete_batch(sel)
                st.rerun()