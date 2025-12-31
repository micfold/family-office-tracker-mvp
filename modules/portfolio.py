# modules/portfolio.py
import pandas as pd
import streamlit as st
import re

# Simple static FX for MVP estimation (CZK Base)
FX_RATES = {'USD': 23.5, 'EUR': 25.2, 'GBP': 29.5, 'CZK': 1.0}


def clean_snowball_number(val):
    """Cleans Snowball export number format (e.g. '1,200.50' or '1.200,50')."""
    if pd.isna(val): return 0.0
    s = str(val).replace('"', '').replace("'", "").strip()
    if not s: return 0.0

    # Simple heuristic for mixed formats
    if ',' in s and '.' in s:
        if s.find(',') > s.find('.'):  # Format: 1.000,00
            s = s.replace('.', '').replace(',', '.')
        else:  # Format: 1,000.00
            s = s.replace(',', '')
    elif ',' in s:
        # If 2 digits after comma, assume decimal (EU style)
        if re.search(r',\d{2}$', s):
            s = s.replace(',', '.')
        else:
            s = s.replace(',', '')

    return float(s)


def process_portfolio(file):
    try:
        df = pd.read_csv(file)

        # 1. Detect Format based on columns
        cols = df.columns.tolist()

        # A. TRANSACTION HISTORY FORMAT (The one causing error)
        if 'Event' in cols and 'Date' in cols:
            return process_history(df)

        # B. HOLDINGS SNAPSHOT FORMAT
        elif 'Current value' in cols:
            return process_snapshot(df)

        else:
            st.error("Unknown Portfolio CSV format. Need 'Event/Date' or 'Current value'.")
            return None

    except Exception as e:
        st.error(f"Portfolio Processing Error: {e}")
        return None


def process_snapshot(df):
    """Logic for Holdings Snapshot."""
    numeric_cols = [
        'Current value', 'Cost basis', 'Total profit', 'Div. received',
        'Dividend yield', 'Next payment', 'Shares', 'Share price'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(clean_snowball_number)

    # Derived Metrics
    if 'Current value' in df.columns and 'Dividend yield' in df.columns:
        df['Projected Annual Divs'] = df['Current value'] * (df['Dividend yield'] / 100)
    else:
        df['Projected Annual Divs'] = 0.0

    total_value = df['Current value'].sum()
    total_projected = df['Projected Annual Divs'].sum()

    return {
        "type": "snapshot",
        "df": df,
        "value": total_value,
        "cost": df['Cost basis'].sum(),
        "profit": df['Total profit'].sum(),
        "divs_earned": df['Div. received'].sum(),
        "divs_projected": total_projected,
        "portfolio_yield": (total_projected / total_value * 100) if total_value else 0,
        "top_10": df.nlargest(10, 'Current value') if 'Current value' in df.columns else pd.DataFrame()
    }


def process_history(df):
    """Logic for Transaction History."""
    # Clean Data
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('Date').copy()

    # Numeric Cleanup
    for col in ['Price', 'Quantity', 'FeeTax']:
        if col in df.columns:
            df[col] = df[col].apply(clean_snowball_number)

    # --- 1. CALCULATE INVESTED CAPITAL CURVE ---
    history_rows = []
    current_holdings = {}  # {Symbol: {'qty': 0, 'total_cost': 0}}
    cumulative_invested_czk = 0.0

    # Pre-calculate FX normalized amounts
    df['FX'] = df['Currency'].map(FX_RATES).fillna(1.0)
    df['AmountCZK'] = df['Price'] * df['Quantity'] * df['FX']

    for idx, row in df.iterrows():
        event = str(row['Event']).upper()
        symbol = row['Symbol']
        qty = row['Quantity']
        amt_czk = row['AmountCZK']

        if event == 'BUY':
            if symbol not in current_holdings: current_holdings[symbol] = {'qty': 0.0, 'total_cost': 0.0}
            current_holdings[symbol]['qty'] += qty
            current_holdings[symbol]['total_cost'] += amt_czk
            cumulative_invested_czk += amt_czk

        elif event == 'SELL':
            if symbol in current_holdings and current_holdings[symbol]['qty'] > 0:
                avg_cost = current_holdings[symbol]['total_cost'] / current_holdings[symbol]['qty']
                cost_of_sold = avg_cost * qty
                current_holdings[symbol]['qty'] -= qty
                current_holdings[symbol]['total_cost'] -= cost_of_sold
                cumulative_invested_czk -= cost_of_sold
                if cumulative_invested_czk < 0: cumulative_invested_czk = 0

        history_rows.append({
            'Date': row['Date'],
            'Invested Capital': cumulative_invested_czk
        })

    history_df = pd.DataFrame(history_rows).drop_duplicates('Date', keep='last')

    # --- 2. DIVIDEND ANALYSIS ---
    div_mask = df['Event'].str.upper().str.contains('DIV')
    div_df = df[div_mask].copy()
    div_df['DividendCZK'] = div_df['AmountCZK']  # Assuming Price column holds Div Amount in export

    div_df['Year'] = div_df['Date'].dt.year
    div_df['Quarter'] = div_df['Date'].dt.to_period('Q').astype(str)

    annual_divs = div_df.groupby('Year')['DividendCZK'].sum().reset_index()
    quarterly_divs = div_df.groupby('Quarter')['DividendCZK'].sum().reset_index()

    total_divs = div_df['DividendCZK'].sum()

    return {
        "type": "history",
        "raw": df,
        "history_df": history_df,
        "annual_divs": annual_divs,
        "quarterly_divs": quarterly_divs,
        "total_invested": cumulative_invested_czk,

        # --- FIX: Standardize Keys for App Compatibility ---
        "value": cumulative_invested_czk,  # PROXY: Use Invested Capital as Value
        "cost": cumulative_invested_czk,
        "profit": 0.0,  # Cannot calc Profit without Market Price
        "divs_earned": total_divs,  # Map to standard key
        "divs_projected": 0.0,  # Cannot calc Yield without Holdings
        "portfolio_yield": 0.0,
        "top_10": pd.DataFrame()
    }