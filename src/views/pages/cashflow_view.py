# src/views/pages/cashflow_view.py
import streamlit as st
from datetime import date
from src.container import get_container
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
            amt = st.number_input("Amount", step=100.0, format="%0.2f")

            # 1. Select Type
            type_options = list(UI_CATEGORIES.keys())
            t_type = st.selectbox("Type", type_options)

            # 2. Select Category (FIXED LOGIC)
            # UI_CATEGORIES[t_type] is now a direct List of strings.
            # We use .get() just to safely handle if the key is missing.
            cat_options = UI_CATEGORIES.get(t_type, ["Uncategorized"])

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
                count, errors = service.process_uploads(files)

                # Show Success
                if count > 0:
                    st.success(f"Processed {count} transactions.")

                # Show Errors
                if errors:
                    for err in errors:
                        st.error(err)

                if count > 0:
                    st.rerun()


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
        if not ledger_df.empty:
            # FIX: Sort by 'date' (lowercase)
            sort_col = 'date' if 'date' in ledger_df.columns else 'Date'
            st.dataframe(ledger_df.sort_values(sort_col, ascending=False), use_container_width=True)
        else:
            st.info("No data found.")

    with tabs[3]:
        history = service.get_batch_history()
        if not history.empty:
            st.dataframe(history, use_container_width=True)
            batch_col = 'Batch_ID' if 'Batch_ID' in history.columns else 'batch_id'
            sel = st.selectbox("Select Batch", history[batch_col].unique())
            if st.button("Delete Batch"):
                service.delete_batch(sel)
                st.rerun()