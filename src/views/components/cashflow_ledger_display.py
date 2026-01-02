import streamlit as st


def render_ledger_display(ledger_df, service, key_suffix: str = "default"):
    if not ledger_df.empty:
        # Normalize columns: prefer lowercase 'date'
        sort_col = 'date' if 'date' in ledger_df.columns else 'Date'
        st.dataframe(ledger_df.sort_values(sort_col, ascending=False), use_container_width=True)
    else:
        st.info("No data found.")

    # Batch management controls
    history = service.get_batch_history()
    if not history.empty:
        st.dataframe(history, use_container_width=True)
        batch_col = 'Batch_ID' if 'Batch_ID' in history.columns else 'batch_id'
        # use a unique key to avoid DuplicateWidgetID when component is used multiple times
        sel = st.selectbox("Select Batch", history[batch_col].unique(), key=f"select_batch_{key_suffix}")
        if st.button("Delete Batch", key=f"delete_batch_{key_suffix}"):
            service.delete_batch(sel)
            st.rerun()
