import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Family Office Command Center", layout="wide")

# --- USER CONSTANTS (Move these to a sidebar settings later) ---
HOUSE_VALUE = 18320000
MORTGAGE_BALANCE = 13000000


# --- CORE LOGIC: PARSING & TAGGING ---
def detect_and_parse(file):
    try:
        df = pd.read_csv(file)
        if len(df.columns) < 2: raise ValueError
    except:
        file.seek(0)
        df = pd.read_csv(file, sep=';')

    cols = df.columns.tolist()
    # Logic for ČS and RB (same as previous training)
    if 'Own account name' in cols:
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Processing Date'], dayfirst=True),
            'Description': df['Partner Name'].fillna('') + " " + df.get('Note', pd.Series([''] * len(df))).fillna(''),
            'Amount': df['Amount'],
            'Source': "Česká spořitelna"
        })
    elif 'Datum provedení' in cols:
        amounts = df['Zaúčtovaná částka'].astype(str).str.replace(' ', '').str.replace(',', '.')
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Datum provedení'], dayfirst=True),
            'Description': df['Název protiúčtu'].fillna('') + " " + df['Zpráva'].fillna(''),
            'Amount': pd.to_numeric(amounts),
            'Source': "Raiffeisenbank"
        })
    elif 'Číslo kreditní karty' in cols:
        amounts = df['Zaúčtovaná částka'].astype(str).str.replace(' ', '').str.replace(',', '.')
        parsed = pd.DataFrame({
            'Date': pd.to_datetime(df['Datum transakce'], dayfirst=True),
            'Description': df['Popis/Místo transakce'].fillna('') + " " + df['Název obchodníka'].fillna(''),
            'Amount': pd.to_numeric(amounts),
            'Source': "RB Credit Card"
        })
    else:
        return None
    return parsed


def auto_tag(row):
    desc = str(row['Description']).lower()
    # 1. Investing (The Reconciliation logic)
    if any(x in desc for x in ['investment', 'trading212', 't212', 'revolut invest', 'broker']):
        return 'Investment Transfer'
    # 2. Fixed OPEX
    if any(x in desc for x in ['mortgage', 'hypoteka', 'vodafone', 'pre', 'cez']):
        return 'Fixed OPEX'
    # 3. Sinking Funds
    if any(x in desc for x in ['shell', 'omv', 'benzina', 'mol', 'servis']):
        return 'Fleet Fund'
    # 4. Living
    if any(x in desc for x in ['albert', 'lidl', 'rohlik', 'globus', 'tesco', 'mcdonald', 'kfc']):
        return 'Living Expenses'
    return 'Uncategorized'


# --- UI LAYOUT ---
st.title("🏛️ Family Office Command Center")

with st.sidebar:
    st.header("1. Data Ingestion")
    bank_files = st.file_uploader("Upload Bank CSVs", type=['csv'], accept_multiple_files=True)
    portfolio_file = st.file_uploader("Upload Portfolio (Snowball Holdings)", type=['csv'])

    st.header("2. Time Controls")
    date_range = st.date_input("Period", [datetime(2023, 1, 1), datetime(2023, 12, 31)])

# --- MAIN ENGINE ---
if bank_files:
    all_data = []
    for f in bank_files:
        parsed = detect_and_parse(f)
        if parsed is not None: all_data.append(parsed)

    ledger = pd.concat(all_data)
    ledger['Date'] = pd.to_datetime(ledger['Date'])
    ledger = ledger[(ledger['Date'].dt.date >= date_range[0]) & (ledger['Date'].dt.date <= date_range[1])]
    ledger['Target Basin'] = ledger.apply(auto_tag, axis=1)

    # --- TAB 1: Net Worth (T-Form) ---
    st.header("I. Balance Sheet (T-Form)")

    # Portfolio Value from CSV
    if portfolio_file:
        port_df = pd.read_csv(portfolio_file)
        # --- PORTFOLIO MODULE ---
        if portfolio_file:
            st.header("📊 Portfolio Intelligence")
            p_df = pd.read_csv(portfolio_file)

            # 1. KPI Calculations
            total_value = p_df['Current value'].sum()
            total_cost = p_df['Cost basis'].sum()
            total_pnl = p_df['Total profit'].sum()
            total_divs = p_df['Div. received'].sum()

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Portfolio Value", f"{total_value:,.0f} CZK")
            col2.metric("Invested Capital", f"{total_cost:,.0f} CZK")
            col3.metric("Total PnL", f"{total_pnl:,.0f} CZK", f"{(total_pnl / total_cost) * 100:.2f}%")
            col4.metric("Dividends Received", f"{total_divs:,.0f} CZK")

            # 2. Top 10 Holdings
            st.subheader("Top 10 Holdings")
            top_10 = p_df.nlargest(10, 'Current value')[['Holding', 'Holdings\' name', 'Current value', 'Total profit']]

            fig_holdings = go.Figure(data=[go.Pie(
                labels=top_10['Holding'],
                values=top_10['Current value'],
                hole=.4,
                hoverinfo="label+percent+value"
            )])
            st.plotly_chart(fig_holdings, use_container_width=True)

            # 3. Sector Distribution
            st.subheader("Sector Exposure")
            sector_dist = p_df.groupby('Sector')['Current value'].sum().reset_index()
            fig_sector = go.Figure(go.Bar(
                x=sector_dist['Current value'],
                y=sector_dist['Sector'],
                orientation='h'
            ))
            st.plotly_chart(fig_sector, use_container_width=True)

            # 4. Data Table (Snowball Style)
            st.subheader("Detailed Asset View")
            st.dataframe(p_df[
                             ['Holding', 'Holdings\' name', 'Shares', 'Cost per share', 'Current value', 'Total profit',
                              'Dividend yield']])
    else:
        current_stocks = 0

    col_assets, col_liabs = st.columns(2)

    with col_assets:
        st.subheader("Assets")
        st.info(f"🏠 Real Estate: {HOUSE_VALUE:,.0f} CZK")
        st.info(f"📈 Portfolio: {current_stocks:,.0f} CZK")
        cash_balance = 400000 + 304000  # Emergency + Sinking
        st.info(f"💵 Cash Reserves: {cash_balance:,.0f} CZK")
        total_assets = HOUSE_VALUE + current_stocks + cash_balance
        st.metric("Total Assets", f"{total_assets:,.0f} CZK")

    with col_liabs:
        st.subheader("Liabilities & Equity")
        st.error(f"📉 Mortgage: {MORTGAGE_BALANCE:,.0f} CZK")
        equity = total_assets - MORTGAGE_BALANCE
        st.success(f"💎 Net Equity: {equity:,.0f} CZK")
        st.metric("Net Worth", f"{equity:,.0f} CZK")

    # --- TAB 2: Cashflow ---
    st.divider()
    st.header("II. Cashflow Waterfall")

    # Aggregating Spending
    spending = ledger[ledger['Amount'] < 0].groupby('Target Basin')['Amount'].sum().abs().reset_index()
    income = ledger[ledger['Amount'] > 0]['Amount'].sum()

    # Create Waterfall Chart
    fig = go.Figure(go.Waterfall(
        name="Flow", orientation="v",
        measure=["relative"] * (len(spending) + 1),
        x=["Total Income"] + list(spending['Target Basin']),
        textposition="outside",
        text=[f"+{income:,.0f}"] + [f"-{v:,.0f}" for v in spending['Amount']],
        y=[income] + list(-spending['Amount']),
        connector={"line": {"color": "rgb(63, 63, 63)"}},
    ))
    st.plotly_chart(fig, use_container_width=True)

    # --- TAB 3: Investment Check ---
    st.divider()
    st.header("III. Investment Activity Check")
    net_invested = ledger[ledger['Target Basin'] == 'Investment Transfer']['Amount'].sum()
    st.metric("Net Capital Injected", f"{net_invested:,.0f} CZK", delta="Money Out of Bank")

    st.write("### Detailed Ledger")
    st.dataframe(ledger.sort_values('Date', ascending=False))