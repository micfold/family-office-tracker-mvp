import pandas as pd
import streamlit as st


def process_portfolio(file):
    try:
        df = pd.read_csv(file)
        # Standardize numeric columns from Snowball CSV
        numeric_cols = [
            'Current value', 'Cost basis', 'Total profit', 'Div. received',
            'Dividend yield', 'Next payment', 'Shares', 'Share price'
        ]
        for col in numeric_cols:
            if col in df.columns:
                # Handle spaces, CZK symbols, and commas
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.-]', '', regex=True).str.replace(',', '.'),
                    errors='coerce'
                ).fillna(0)

        metrics = {
            "df": df,
            "value": df['Current value'].sum(),
            "cost": df['Cost basis'].sum(),
            "profit": df['Total profit'].sum(),
            "divs": df['Div. received'].sum(),
            "next_div": df['Next payment'].sum() if 'Next payment' in df.columns else 0,
            "top_10": df.nlargest(10, 'Current value') if 'Current value' in df.columns else pd.DataFrame()
        }
        return metrics
    except Exception as e:
        st.error(f"Portfolio Processing Error: {e}")
        return None