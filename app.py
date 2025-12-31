import streamlit as st
import pandas as pd
from data_logic.bank_parser import detect_and_parse_bank, apply_tagging, apply_magic_rules
from data_logic.portfolio_pro import process_portfolio
from components.visuals import render_t_form, render_waterfall, render_portfolio_visuals

st.set_page_config(page_title="Family Office HQ", layout="wide")

with st.sidebar:
    st.title("🏛️ Control Tower")
    bank_files = st.file_uploader("Upload Bank Statements", type=['csv'], accept_multiple_files=True)
    port_file = st.file_uploader("Upload Snowball CSV", type=['csv'])
    st.divider()
    st.header("Asset Valuation")
    house_val = st.number_input("House Value", value=18320000)
    fleet_val = st.number_input("Fleet Value", value=1500000)
    mortgage_val = st.number_input("Mortgage Balance", value=13000000)
    st.header("Cash Breakdown")
    cash_dict = {
        "Emergency Fund": st.number_input("Emergency Fund", value=400000),
        "Fleet Sinking Fund": st.number_input("Fleet Sinking Fund", value=100000),
        "Partner SLA": st.number_input("Partner SLA", value=99000),
        "Health & House": st.number_input("Health & House Fund", value=75000),
        "Junior Fund": st.number_input("Junior Fund", value=30000)
    }

tabs = st.tabs(["💎 Net Worth", "💸 Cashflow", "📊 Portfolio", "📜 Ledger"])

stocks_val = 0
if port_file:
    p_metrics = process_portfolio(port_file)
    if p_metrics:
        stocks_val = p_metrics['value']
        with tabs[2]:
            render_portfolio_visuals(p_metrics)
            st.dataframe(p_metrics['df'])

if bank_files:
    raw_dfs = []
    for f in bank_files:
        parsed = detect_and_parse_bank(f)
        # Check that the file was recognized AND contains data
        if parsed is not None and not parsed.empty:
            raw_dfs.append(parsed)

    # NEW: Only concatenate if we have recognized data
    if len(raw_dfs) > 0:
        ledger = apply_tagging(pd.concat(raw_dfs))
        with tabs[1]:
            st.header("Monthly Cashflow Waterfall")
            income = ledger[ledger['Amount'] > 0]['Amount'].sum()
            spend = ledger[ledger['Amount'] < 0].groupby('Target Basin')['Amount'].sum().abs().reset_index()
            render_waterfall(income, spend)
        with tabs[3]:
            st.header("Consolidated Transaction Ledger")
            st.dataframe(ledger.sort_values('Date', ascending=False))
    else:
        with tabs[1]:
            st.warning(
                "No valid transactions recognized in the uploaded files. Please check if you are using the correct bank CSVs.")

# --- SIDEBAR MAGIC RULES ---
if 'rules' not in st.session_state:
    st.session_state.rules = [
        {'pattern': 'Trading 212', 'target': 'Investing'},
        {'pattern': 'Albert', 'target': 'Living (Groceries)'},
        {'pattern': 'Hypoteka', 'target': 'Fixed OPEX (Mortgage)'}
    ]

with st.expander("✨ Magic Categorization Rules"):
    new_pattern = st.text_input("Vendor/Description Pattern")
    new_target = st.selectbox("Assign to Basin",
                              ["Investing", "Living (Groceries)", "Fleet Fund", "Fixed OPEX", "Health Fund"])
    if st.button("Add Rule"):
        st.session_state.rules.append({'pattern': new_pattern, 'target': new_target})

    st.write("Current Rules:")
    for i, r in enumerate(st.session_state.rules):
        st.text(f"{r['pattern']} -> {r['target']}")
        if st.button(f"Remove Rule {i}"):
            st.session_state.rules.pop(i)
            st.rerun()

# When processing ledger:
if bank_files and 'raw_dfs' in dir() and len(raw_dfs) > 0:
    ledger = apply_magic_rules(pd.concat(raw_dfs), st.session_state.rules)

with tabs[0]:
    render_t_form(house_val, fleet_val, stocks_val, cash_dict, mortgage_val)