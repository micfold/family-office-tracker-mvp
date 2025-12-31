import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION ---
st.set_page_config(page_title="Family Office HQ", layout="wide")


# --- LOGIC: BANK RECOGNITION ---
def detect_bank_format(df):
    cols = [c.lower() for c in df.columns]

    # Example Logic (You will expand this)
    if 'datum' in cols and 'částka' in cols:
        return "Ceska Sporitelna / Local Bank"
    elif 'transaction date' in cols and 'description' in cols:
        return "Revolut / International"
    else:
        return "Unknown Format"


def process_ledger(df, bank_type):
    # This standardizes different bank CSVs into your "Master Ledger" format
    ledger = pd.DataFrame()

    if bank_type == "Revolut / International":
        ledger['Date'] = pd.to_datetime(df['Transaction Date'])
        ledger['Amount'] = df['Amount']  # Assuming negative for spend
        ledger['Description'] = df['Description']

    elif bank_type == "Ceska Sporitelna / Local Bank":
        ledger['Date'] = pd.to_datetime(df['Datum'], dayfirst=True)
        ledger['Amount'] = df['Částka']
        ledger['Description'] = df['Název protiúčtu'].fillna(df['Poznámka'])

    else:
        st.error("Bank format not supported yet.")
        return None

    # Auto-Tagging Logic (Simple MVP Version)
    ledger['Category'] = 'Uncategorized'
    ledger.loc[ledger['Description'].str.contains('MORTGAGE|HYPOTEKA', case=False,
                                                  na=False), 'Category'] = 'Fixed OPEX (Mortgage)'
    ledger.loc[ledger['Description'].str.contains('LIDL|ALBERT|ROHLIK', case=False,
                                                  na=False), 'Category'] = 'Living (Groceries)'
    ledger.loc[ledger['Description'].str.contains('SHELL|OMV|BENZINA', case=False, na=False), 'Category'] = 'Fleet Fund'

    return ledger


# --- UI: SIDEBAR ---
st.sidebar.title(" CFO Controls")
uploaded_file = st.sidebar.file_uploader("Upload Bank Statement (CSV)", type=['csv'])

# --- UI: MAIN DASHBOARD ---
st.title("Family Office Command Center")

if uploaded_file is not None:
    # 1. Read File
    df_raw = pd.read_csv(uploaded_file)
    st.write("### 1. Raw Data Detected")
    st.dataframe(df_raw.head())

    # 2. Detect Bank
    bank_type = detect_bank_format(df_raw)
    st.info(f"Detected Bank Format: **{bank_type}**")

    # 3. Process to Ledger
    if bank_type != "Unknown Format":
        ledger = process_ledger(df_raw, bank_type)

        # 4. Show Analysis
        if ledger is not None:
            col1, col2, col3 = st.columns(3)
            total_spend = ledger[ledger['Amount'] < 0]['Amount'].sum()
            total_income = ledger[ledger['Amount'] > 0]['Amount'].sum()

            col1.metric("Total Income", f"{total_income:,.0f} CZK")
            col2.metric("Total Spend", f"{total_spend:,.0f} CZK")
            col3.metric("Net Flow", f"{total_income + total_spend:,.0f} CZK")

            st.write("### 2. Auto-Categorized Ledger")
            st.dataframe(ledger)

            # 5. The Waterfall Visual
            st.write("### 3. Spending Waterfall")
            spending_by_cat = ledger[ledger['Amount'] < 0].groupby('Category')['Amount'].sum().abs().reset_index()

            fig = go.Figure(go.Bar(
                x=spending_by_cat['Amount'],
                y=spending_by_cat['Category'],
                orientation='h'
            ))
            st.plotly_chart(fig)

else:
    st.info("Waiting for Bank Statement... Upload CSV in the sidebar.")