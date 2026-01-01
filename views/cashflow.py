# views/cashflow.py
import streamlit as st
import pandas as pd
from datetime import date
from services.ledger import LedgerService
from core.enums import ExpenseCategory, IncomeCategory, TransactionType, CATEGORY_METADATA
from modules import analytics, processing
from components import visuals


def render_view():
    st.title("💸 Cashflow & Ledger")

    service = LedgerService()
    ledger_df = service.load_ledger()

    # Use state to control tab switching if needed
    if 'active_tab' not in st.session_state: st.session_state.active_tab = "entry"

    # Create the 4 main tabs from Master
    tabs = st.tabs(["📥 Entry & Upload", "🛠️ Data Quality", "⚖️ Reconciliation", "📜 Ledger Data"])

    # --- TAB 1: ENTRY ---
    with tabs[0]:
        c1, c2 = st.columns(2)

        # Manual Entry
        with c1:
            st.subheader("Manual Entry")
            with st.form("manual_add"):
                d = st.date_input("Date", date.today())
                desc = st.text_input("Description")
                amt = st.number_input("Amount", step=100.0)

                # Dynamic Type/Category
                t_type = st.selectbox("Type", list(CATEGORY_METADATA.keys()))
                cat = st.selectbox("Category", CATEGORY_METADATA[t_type])

                if st.form_submit_button("Add Transaction"):
                    new_row = {
                        'Date': pd.to_datetime(d),
                        'Description': desc,
                        'Amount': amt,
                        'Currency': 'CZK',
                        'Category': cat,
                        'Type': t_type,
                        'Source': 'Manual'
                    }
                    updated = pd.concat([ledger_df, pd.DataFrame([new_row])], ignore_index=True)
                    service.save_ledger(updated)
                    st.success("Added!")
                    st.rerun()

        # Batch Upload
        with c2:
            st.subheader("Batch Upload")
            files = st.file_uploader("Bank CSVs/ZIPs", accept_multiple_files=True)
            if files and st.button("Process Files"):
                new_df = service.process_upload(files)
                if not new_df.empty:
                    combined = pd.concat([ledger_df, new_df]).drop_duplicates()
                    service.save_ledger(combined)
                    st.success(f"Imported {len(new_df)} transactions!")
                    st.rerun()

    # --- TAB 2: DATA QUALITY (Restored) ---
    with tabs[1]:
        st.subheader("Data Quality Workbench")
        if not ledger_df.empty:
            # Suggestions
            sug = processing.suggest_patterns(ledger_df)
            if not sug.empty:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("#### Uncategorized Patterns")
                    st.dataframe(sug[['Description', 'Count', 'Total_Value']], width='stretch')
                with c2:
                    st.info("💡 Tip: Add these patterns to `core/config.py` to auto-categorize them in the future.")
            else:
                st.success("No recurring uncategorized patterns found!")

            st.divider()
            st.markdown("#### Uncategorized Transactions")
            uncat = ledger_df[ledger_df['Category'] == 'Uncategorized']
            st.dataframe(uncat, width='stretch')
        else:
            st.info("Ledger is empty.")

    # --- TAB 3: RECONCILIATION (Restored) ---
    with tabs[2]:
        st.subheader("Balance Reconciliation")
        if not ledger_df.empty:
            c1, c2 = st.columns([1, 3])
            with c1:
                chk_date = st.date_input("Checkpoint Date", value=date.today())
                chk_bal = st.number_input("Balance on Date", value=0.0)

            # Logic: Calculate running balance
            rec_df = analytics.calculate_running_balance(ledger_df, chk_date, chk_bal)
            visuals.render_balance_history(rec_df)
        else:
            st.info("Ledger is empty.")

    # --- TAB 4: DATA ---
    with tabs[3]:
        st.dataframe(ledger_df, width='stretch')