# views/cashflow.py
import streamlit as st
import pandas as pd
from datetime import date
from services.ledger import LedgerService
from core.enums import CATEGORY_METADATA
from core.config import GLOBAL_RULES, UI_CATEGORIES
from modules import analytics, processing
from components import visuals


def render_view():
    st.title("💸 Cashflow & Ledger")

    service = LedgerService()
    ledger_df = service.load_ledger()
    user_rules = service.load_user_rules()

    # Create 5 tabs (Added Reporting)
    tabs = st.tabs(["📥 Entry & Upload", "🛠️ Data Quality", "⚖️ Reconciliation", "📊 Reporting", "📜 Ledger Data"])

    # --- TAB 1: ENTRY ---
    with tabs[0]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Manual Entry")
            with st.form("manual_add"):
                d = st.date_input("Date", date.today())
                desc = st.text_input("Description")
                amt = st.number_input("Amount", step=100.0)
                t_type = st.selectbox("Type", list(CATEGORY_METADATA.keys()))
                cat = st.selectbox("Category", CATEGORY_METADATA[t_type])

                if st.form_submit_button("Add Transaction"):
                    new_row = {
                        'Date': pd.to_datetime(d), 'Description': desc, 'Amount': amt,
                        'Currency': 'CZK', 'Category': cat, 'Type': t_type, 'Source': 'Manual'
                    }
                    updated = pd.concat([ledger_df, pd.DataFrame([new_row])], ignore_index=True)
                    service.save_ledger(updated)
                    st.success("Added!")
                    st.rerun()

        with c2:
            st.subheader("Batch Upload")
            files = st.file_uploader("Bank CSVs/ZIPs", accept_multiple_files=True)
            if files and st.button("Process Files"):
                new_df = service.process_upload(files, user_rules)

                if not new_df.empty:
                    if ledger_df.empty:
                        combined = new_df
                    else:
                        combined = pd.concat([ledger_df, new_df], ignore_index=True)

                    # Remove duplicates and save
                    combined = combined.drop_duplicates()
                    service.save_ledger(combined)

                    st.success(f"Imported {len(new_df)} transactions!")
                    st.rerun()

    # --- TAB 2: DATA QUALITY ---
    with tabs[1]:
        st.subheader("Data Quality Workbench")
        if not ledger_df.empty:
            sug = processing.suggest_patterns(ledger_df)

            if not sug.empty:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("#### Uncategorized Patterns")
                    # Added selection_mode to enable interaction
                    st.dataframe(
                        sug[['Description', 'Count', 'Total_Value']],
                        width='stretch',
                        selection_mode="single-row",
                        on_select="rerun",
                        key="suggestion_table"
                    )

                with c2:
                    st.markdown("#### Quick Rule Creator")
                    # Check if user selected a row
                    if "suggestion_table" in st.session_state and st.session_state.suggestion_table.selection.rows:
                        row_idx = st.session_state.suggestion_table.selection.rows[0]
                        sel_desc = sug.iloc[row_idx]['Description']

                        st.write(f"**Pattern:** `{sel_desc}`")

                        # Rule Creation Form
                        qr_type = st.selectbox("Type", list(UI_CATEGORIES.keys()), key="qr_type_sel")
                        with st.form("quick_rule"):
                            qr_cat = st.selectbox("Category", UI_CATEGORIES[qr_type])
                            if st.form_submit_button("Create Rule"):
                                new_rule = {'pattern': sel_desc, 'target': qr_cat}
                                user_rules.append(new_rule)
                                service.save_user_rules(user_rules)

                                # Re-process ledger to apply new rule immediately
                                reprocessed = processing.apply_categorization(ledger_df, GLOBAL_RULES, user_rules)
                                service.save_ledger(reprocessed)

                                st.success("Rule Saved & Ledger Updated!")
                                st.rerun()
                    else:
                        st.info("👈 Select a pattern to create a rule.")
            else:
                st.success("No recurring uncategorized patterns found!")

            st.divider()
            st.markdown(f"#### Uncategorized Transactions")
            st.dataframe(ledger_df[ledger_df['Category'] == 'Uncategorized'], width='stretch')
        else:
            st.info("Ledger is empty.")

    # --- TAB 3: RECONCILIATION ---
    with tabs[2]:
        st.subheader("Balance Reconciliation")
        if not ledger_df.empty:
            c1, c2 = st.columns([1, 3])
            with c1:
                chk_date = st.date_input("Checkpoint Date", value=date.today())
                chk_bal = st.number_input("Balance on Date", value=0.0)
            rec_df = analytics.calculate_running_balance(ledger_df, chk_date, chk_bal)
            visuals.render_balance_history(rec_df)

    # --- TAB 4: REPORTING ---
    with tabs[3]:
        st.subheader("Financial Analytics")
        if not ledger_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                visuals.render_pie(
                    analytics.get_expense_breakdown(ledger_df),
                    'AbsAmount', 'Category', "Expenses by Category"
                )
            with c2:
                visuals.render_bar(
                    analytics.get_fixed_vs_variable(ledger_df),
                    'Type', 'AbsAmount', "Fixed vs Variable", color='Type'
                )
        else:
            st.info("No data available.")

    # --- TAB 5: DATA ---
    with tabs[4]:
        st.dataframe(ledger_df.sort_values('Date', ascending=False), width='stretch')