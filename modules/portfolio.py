# modules/portfolio.py
import pandas as pd
import streamlit as st


def process_portfolio(file):
    try:
        # Load Data
        df = pd.read_csv(file)

        # Numeric Cleanup
        numeric_cols = [
            'Current value', 'Cost basis', 'Total profit', 'Div. received',
            'Dividend yield', 'Next payment', 'Shares', 'Share price'
        ]

        for col in numeric_cols:
            if col in df.columns:
                # Remove currency symbols, spaces, handle comma decimals
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.,-]', '', regex=True).str.replace(',', '.'),
                    errors='coerce'
                ).fillna(0)

        # --- NEW INSIGHTS ---
        # 1. Projected Annual Dividend: Value * (Yield / 100)
        # Note: Snowball export "Dividend yield" is usually percent (e.g., 4.5)
        if 'Current value' in df.columns and 'Dividend yield' in df.columns:
            df['Projected Annual Divs'] = df['Current value'] * (df['Dividend yield'] / 100)
        else:
            df['Projected Annual Divs'] = 0.0

        total_value = df['Current value'].sum()
        total_projected_div = df['Projected Annual Divs'].sum()
        total_realized_div = df['Div. received'].sum()

        # Weighted Average Yield
        portfolio_yield = (total_projected_div / total_value * 100) if total_value > 0 else 0

        metrics = {
            "df": df,
            "value": total_value,
            "cost": df['Cost basis'].sum(),
            "profit": df['Total profit'].sum(),
            "divs_earned": total_realized_div,
            "divs_projected": total_projected_div,
            "portfolio_yield": portfolio_yield,
            "top_10": df.nlargest(10, 'Current value')
        }
        return metrics
    except Exception as e:
        st.error(f"Portfolio Processing Error: {e}")
        return None