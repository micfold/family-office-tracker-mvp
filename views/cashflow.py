# views/cashflow.py
import streamlit as st
import pandas as pd
from datetime import date
from services.ledger import LedgerService
from core.enums import ExpenseCategory, IncomeCategory, TransactionType


def render_view():
    st.title("💸 Cashflow & Ledger")

    service = LedgerService()
    ledger_df = service.load_ledger()

    tab1, tab2 = st.tabs(["📥 Upload & Entry", "📜 Ledger Data"])

    with tab1:
        c1, c2 = st.columns(2)

        # Manual Entry
        with c1:
            st.subheader("Manual Entry")
            with st.form("manual_add"):
                d = st.date_input("Date", date.today())
                desc = st.text_input("Description")
                amt = st.number_input("Amount", step=100.0)

                # Dynamic Selectbox based on Enums
                t_type = st.selectbox("Type", [t.value for t in TransactionType])

                cat_options = []
                if t_type == TransactionType.EXPENSE.value:
                    cat_options = [e.value for e in ExpenseCategory]
                elif t_type == TransactionType.INCOME.value:
                    cat_options = [e.value for e in IncomeCategory]

                cat = st.selectbox("Category", cat_options)

                if st.form_submit_button("Add Transaction"):
                    new_row = {
                        'Date': pd.to_datetime(d),
                        'Description': desc,
                        'Amount': amt,  # Ensure logic handles sign conventions
                        'Currency': 'CZK',
                        'Category': cat,
                        'Type': t_type,
                        'Source': 'Manual'
                    }
                    updated = pd.concat([ledger_df, pd.DataFrame([new_row])], ignore_index=True)
                    service.save_ledger(updated)
                    st.success("Added!")
                    st.rerun()

        # File Upload
        with c2:
            st.subheader("Batch Upload")
            files = st.file_uploader("Bank CSVs", accept_multiple_files=True)
            if files and st.button("Process Files"):
                new_df = service.process_upload(files)
                if not new_df.empty:
                    combined = pd.concat([ledger_df, new_df]).drop_duplicates()
                    service.save_ledger(combined)
                    st.success(f"Imported {len(new_df)} transactions!")
                    st.rerun()

    with tab2:
        st.dataframe(ledger_df, width='stretch')