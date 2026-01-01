# views/cashflow.py
import streamlit as st
import pandas as pd
from datetime import date
from services.ledger import LedgerService
from src.domain.enums import CATEGORY_METADATA
from config import UI_CATEGORIES


def render_view():
    st.title("💸 Cashflow & Ledger")

    service = LedgerService()
    ledger_df = service.load_ledger()

    tabs = st.tabs(["📥 Entry & Upload", "🛠️ Data Quality", "⚖️ Reconciliation", "📊 Reporting", "📜 Ledger Data"])

    # --- TAB 1: ENTRY & UPLOAD ---
    with tabs[0]:
        c1, c2 = st.columns(2)

        # 1. Manual Entry
        with c1:
            st.subheader("Manual Entry")
            with st.form("manual_add"):
                d = st.date_input("Date", date.today())
                desc = st.text_input("Description")
                amt = st.number_input("Amount", step=100.0)
                t_type = st.selectbox("Type", list(CATEGORY_METADATA.keys()))
                cat = st.selectbox("Category", CATEGORY_METADATA[t_type])  # Assuming fixed struct

                # New Account Fields
                src = st.text_input("Source Account")
                tgt = st.text_input("Target Account")

                if st.form_submit_button("Add Transaction"):
                    new_row = {
                        'Date': pd.to_datetime(d),
                        'Description': desc,
                        'Amount': amt,
                        'Currency': 'CZK',
                        'Category': cat,
                        'Type': t_type,
                        'Source': 'Manual',
                        'Source_Account': src,
                        'Target_Account': tgt,
                        'Batch_ID': 'Manual'
                    }
                    updated = pd.concat([ledger_df, pd.DataFrame([new_row])], ignore_index=True)
                    service.save_ledger(updated)
                    st.success("Added!")
                    st.rerun()

        # 2. Batch Upload
        with c2:
            st.subheader("Batch Upload")
            files = st.file_uploader("Bank CSVs/ZIPs", accept_multiple_files=True)

            if files and st.button("Process Files"):
                with st.spinner("Processing..."):
                    new_df = service.process_upload(files)

                    if not new_df.empty:
                        # Business Logic Deduplication:
                        # We identify duplicates based on the ACTUAL content, ignoring the Batch_ID
                        # This prevents "Double Counting" if you upload the same file twice without deleting

                        subset_cols = ['Date', 'Description', 'Amount', 'Source_Account']

                        # 1. Combine old and new
                        if ledger_df.empty:
                            combined = new_df
                        else:
                            combined = pd.concat([ledger_df, new_df], ignore_index=True)

                        # 2. Remove duplicates based on content, keeping the LAST upload (the new one)
                        # This updates the Batch_ID if you are re-uploading existing data
                        before_count = len(combined)
                        combined = combined.drop_duplicates(subset=subset_cols, keep='last')
                        after_count = len(combined)

                        duplicates_removed = before_count - after_count

                        # 3. Save
                        service.save_ledger(combined)

                        msg = f"✅ Processed {len(new_df)} rows."
                        if duplicates_removed > 0:
                            msg += f" (Updated {duplicates_removed} existing transactions)"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.warning("⚠️ No valid transactions found in the uploaded files. Check file format.")

    # --- TAB 2: DATA QUALITY (With Rule Manager) ---
    with tabs[1]:
        # ... (Keep existing Data Quality code)
        pass

        # --- TAB 3: RECONCILIATION ---
    with tabs[2]:
        # ... (Keep existing Reconciliation code)
        pass

    # --- TAB 4: REPORTING ---
    with tabs[3]:
        # ... (Keep existing Reporting code)
        pass

    # --- TAB 5: LEDGER DATA ---
    with tabs[4]:
        # ... (Keep existing Ledger Data code)
        pass

    # --- BELOW TABS: UPLOAD HISTORY & MANAGEMENT ---
    st.divider()
    st.subheader("📂 Upload History")

    history = service.get_batch_history()

    if not history.empty:
        st.dataframe(
            history.style.format({
                'Total_In': "{:,.0f}",
                'Total_Out': "{:,.0f}"
            }),
            width='stretch',
            column_config={
                "Batch_ID": "Import ID",
                "Tx_Count": "Transactions",
                "Total_In": "Total Income",
                "Total_Out": "Total Outgoing"
            }
        )

        st.write("### Manage Batch")

        # Action Selector
        selected_batch = st.selectbox(
            "Select Batch to Edit/Delete",
            history['Batch_ID'].unique(),
            key="batch_selector"
        )

        col_a, col_b = st.columns(2)

        # DELETE
        with col_a:
            if st.button("🗑️ Delete Entire Batch", type="primary", width='stretch'):
                service.delete_batch(selected_batch)
                st.warning(f"Batch {selected_batch} deleted.")
                st.rerun()

        # EDIT
        with col_b:
            if st.button("✏️ Edit Transactions", width='stretch'):
                st.session_state['editing_batch'] = selected_batch

        # EDITOR INTERFACE
        if st.session_state.get('editing_batch') == selected_batch:
            st.markdown(f"#### 📝 Editing: {selected_batch}")

            # Load fresh data
            current_full = service.load_ledger()
            batch_data = current_full[current_full['Batch_ID'] == selected_batch].copy()

            # Generate options list for the SelectboxColumn
            # Flatten the dictionary values into a single list of strings
            cat_options = []
            for group in UI_CATEGORIES.values():
                cat_options.extend(group)

            edited_batch = st.data_editor(
                batch_data,
                num_rows="dynamic",
                width='stretch',
                key="editor_grid",
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="YYYY-MM-DD"),
                    "Amount": st.column_config.NumberColumn("Amount", format="%.2f"),
                    # FIXED: Changed SelectColumn to SelectboxColumn
                    "Category": st.column_config.SelectboxColumn(
                        "Category",
                        options=cat_options,
                        required=True
                    ),
                    "Batch_ID": st.column_config.TextColumn("Batch ID", disabled=True)
                }
            )

            if st.button("💾 Save Changes"):
                # Filter OUT the old batch data
                remaining_data = current_full[current_full['Batch_ID'] != selected_batch]

                # Combine remaining + edited
                updated_ledger = pd.concat([remaining_data, edited_batch], ignore_index=True)

                service.save_ledger(updated_ledger)
                st.success("Batch updated successfully!")
                del st.session_state['editing_batch']
                st.rerun()

    else:
        st.caption("No upload history available.")