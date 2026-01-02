import streamlit as st
import pandas as pd


def _style_ledger(df: pd.DataFrame):
    """
    Applies styling to the ledger DataFrame for better readability.
    """
    def style_row(row):
        style = ''
        if row.get('is_internal'):
            style = 'background-color: lightblue'
        elif row.get('is_duplicate'):
            style = 'background-color: lightcoral'
        return [style] * len(row)

    styler = df.style.apply(style_row, axis=1)

    styler.format({
        "date": lambda x: x.strftime("%Y-%m-%d") if isinstance(x, pd.Timestamp) else x,
        "amount": "{:,.2f}",
        "confidence": "{:.2%}"
    })

    return styler


def render_ledger_display(ledger_df, service, key_suffix: str = "default"):
    if not ledger_df.empty:
        # Normalize columns: prefer lowercase 'date'
        sort_col = 'date' if 'date' in ledger_df.columns else 'Date'

        # Columns to display
        display_cols = [
            "date", "description", "amount", "category", "account",
            "is_internal", "suggested_category", "confidence"
        ]

        # Filter out columns that don't exist in the DataFrame
        existing_cols = [col for col in display_cols if col in ledger_df.columns]

        display_df = ledger_df[existing_cols].sort_values(sort_col, ascending=False)

        st.dataframe(_style_ledger(display_df), use_container_width=True)
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
