import pandas as pd
import re

# Restored Static FX
FX_RATES = {'USD': 23.5, 'EUR': 25.2, 'GBP': 29.5, 'CZK': 1.0}


def clean_numeric(val):
    if pd.isna(val): return 0.0
    # Extract only digits, dots, commas, and minus signs
    s = re.sub(r'[^\d.,-]', '', str(val))
    if not s: return 0.0

    # Heuristic for decimal separators
    if ',' in s and '.' in s:
        # Keep the later one as decimal, remove the earlier one
        if s.find('.') > s.find(','):
            s = s.replace(',', '')
        else:
            s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        # If only a comma exists, treat it as a decimal (European standard)
        s = s.replace(',', '.')

    return float(s)

def process_portfolio_file(file_obj):
    """Determines type and processes."""
    try:
        file_obj.seek(0)
        df = pd.read_csv(file_obj)
        cols = df.columns.tolist()

        if 'Event' in cols and 'Date' in cols:
            return process_history(df)
        elif 'Current value' in cols:
            return process_snapshot(df)
        else:
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def process_snapshot(df):
    numeric_cols = ['Current value', 'Cost basis', 'Total profit', 'Div. received', 'Dividend yield']
    for col in numeric_cols:
        if col in df.columns: df[col] = df[col].apply(clean_numeric)

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
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.sort_values('Date').copy()

    for col in ['Price', 'Quantity', 'FeeTax']:
        if col in df.columns: df[col] = df[col].apply(clean_numeric)

    history_rows = []
    current_holdings = {}
    cumulative_invested_czk = 0.0

    df['FX'] = df['Currency'].map(FX_RATES).fillna(1.0)
    df['AmountCZK'] = df['Price'] * df['Quantity'] * df['FX']

    for idx, row in df.iterrows():
        event = str(row['Event']).upper()
        symbol = row['Symbol']
        qty = row['Quantity']
        amt_czk = row['AmountCZK']

        if event == 'BUY':
            if symbol not in current_holdings: current_holdings[symbol] = {'qty': 0.0, 'cost': 0.0}
            current_holdings[symbol]['qty'] += qty
            current_holdings[symbol]['cost'] += amt_czk
            cumulative_invested_czk += amt_czk

        elif event == 'SELL':
            if symbol in current_holdings and current_holdings[symbol]['qty'] > 0:
                avg_cost = current_holdings[symbol]['cost'] / current_holdings[symbol]['qty']
                cost_of_sold = avg_cost * qty
                current_holdings[symbol]['qty'] -= qty
                current_holdings[symbol]['cost'] -= cost_of_sold
                cumulative_invested_czk -= cost_of_sold
                if cumulative_invested_czk < 0: cumulative_invested_czk = 0

        history_rows.append({'Date': row['Date'], 'Invested Capital': cumulative_invested_czk})

    history_df = pd.DataFrame(history_rows).drop_duplicates('Date', keep='last')

    div_mask = df['Event'].str.upper().str.contains('DIV')
    div_df = df[div_mask].copy()
    div_df['DividendCZK'] = div_df['AmountCZK']
    div_df['Year'] = div_df['Date'].dt.year
    div_df['Quarter'] = div_df['Date'].dt.to_period('Q').astype(str)

    return {
        "type": "history",
        "raw": df,
        "history_df": history_df,
        "annual_divs": div_df.groupby('Year')['DividendCZK'].sum().reset_index(),
        "quarterly_divs": div_df.groupby('Quarter')['DividendCZK'].sum().reset_index(),
        "total_invested": cumulative_invested_czk,
        "divs_earned": div_df['DividendCZK'].sum(),
        "value_proxy": cumulative_invested_czk
    }