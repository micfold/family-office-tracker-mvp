import streamlit as st
from datetime import date


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
            type_options = list(service.ui_categories.keys()) if hasattr(service, 'ui_categories') else ["Expense", "Income"]
            t_type = st.selectbox("Type", type_options)

            # 2. Select Category (FIXED LOGIC)
            cat_options = service.ui_categories.get(t_type, ["Uncategorized"]) if hasattr(service, 'ui_categories') else ["Uncategorized"]
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

