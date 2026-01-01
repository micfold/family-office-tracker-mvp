import streamlit as st
import pandas as pd
from datetime import date
from src.application.ledger_service import LedgerService
from src.domain.repositories.sql_repository import SqlTransactionRepository
from src.domain.enums import CATEGORY_METADATA, TransactionType
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
            t_type = st.selectbox("Type", list(CATEGORY_METADATA.keys()))
            cat = st.selectbox("Category", CATEGORY_METADATA[t_type]['class'])  # Fix access if structure differs

            if st.form_submit_button("Add Transaction"):
                service.add_manual_transaction({
                    'date': d,
                    'description': desc,
                    'amount': amt,
                    'category': cat,
                    'type': t_type,
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


def render_ledger_data_tab(ledger_df):
    if not ledger_df.empty:
        # We use Data Editor to allow quick fixes
        # Note: Implementing write-back from Data Editor to Repo requires extra wiring
        # For now, read-only with sort
        st.dataframe(ledger_df.sort_values('Date', ascending=False), use_container_width=True)
    else:
        st.info("Ledger is empty.")


def render_batch_management_tab(service):
    history = service.get_batch_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)

        selected_batch = st.selectbox("Select Batch to Delete", history['Batch_ID'].unique())
        if st.button("🗑️ Delete Batch", type="primary"):
            service.delete_batch(selected_batch)
            st.warning(f"Deleted batch {selected_batch}")
            st.rerun()


def render_view():
    st.title("💸 Cashflow & Ledger (Refactored)")

    # Dependency Injection
    repo = SqlTransactionRepository()
    service = LedgerService(repo)

    # Load Data
    ledger_df = service.get_recent_transactions()

    tabs = st.tabs(["📥 Entry & Upload", "📜 Ledger Data", "📂 Batch Management"])

    # --- TAB 1: ENTRY & UPLOAD ---
    with tabs[0]:
        render_entry_upload_tab(service)

    # --- TAB 2: DATA GRID ---
    with tabs[1]:
        render_ledger_data_tab(ledger_df)

    # --- TAB 3: BATCH MANAGEMENT ---
    with tabs[2]:
        render_batch_management_tab(service)
