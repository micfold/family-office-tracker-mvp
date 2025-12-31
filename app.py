# app.py
import streamlit as st
import pandas as pd
import os
import datetime
from config.settings import DEFAULT_RULES, DEFAULT_PORTFOLIO_FILE
from modules import ingestion, processing, analytics, portfolio
from components import visuals

st.set_page_config(page_title="Family Office HQ", layout="wide", page_icon="🏛️")

# --- INITIALIZATION ---
if 'rules' not in st.session_state: st.session_state.rules = DEFAULT_RULES
if 'ledger' not in st.session_state: st.session_state.ledger = pd.DataFrame()
if 'assets' not in st.session_state:
    st.session_state.assets = {
        'house': 18320000, 'fleet': 1500000, 'mortgage': 13000000,
        'cash': {'Emergency': 400000, 'Fleet Sinking': 100000, 'Living': 99000}
    }


# Load Portfolio
@st.cache_data
def load_local_data(path):
    return portfolio.process_portfolio(path) if os.path.exists(path) else None


if 'portfolio_metrics' not in st.session_state:
    local_data = load_local_data(DEFAULT_PORTFOLIO_FILE)
    st.session_state.portfolio_metrics = local_data
    st.session_state.portfolio_source = "📍 Local File" if local_data else None

# --- GLOBALS ---
p_metrics = st.session_state.portfolio_metrics
stocks_val = p_metrics['value'] if p_metrics else 0.0
assets = st.session_state.assets
total_cash = sum(assets['cash'].values())
total_assets = assets['house'] + assets['fleet'] + stocks_val + total_cash
net_worth = total_assets - assets['mortgage']

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Control Tower")
    nav = st.radio("Navigate to:",
                   ["Dashboard Overview", "Assets & Liabilities", "Cashflow & Ledger", "Investment Portfolio"])
    st.divider()
    if st.session_state.portfolio_metrics: st.success(f"Portfolio: {st.session_state.portfolio_source}")
    if not st.session_state.ledger.empty: st.success(f"Ledger: {len(st.session_state.ledger)} Tx")

# --- VIEWS ---

# 1. DASHBOARD
if nav == "Dashboard Overview":
    st.header("📊 Executive Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Net Worth", f"{net_worth:,.0f} CZK")
    c2.metric("Total Assets", f"{total_assets:,.0f} CZK")
    c3.metric("Liquid Cash", f"{total_cash:,.0f} CZK")
    c4.metric("Investments", f"{stocks_val:,.0f} CZK")

    st.divider()

    if not st.session_state.ledger.empty:
        inc, exp, net = analytics.get_net_cashflow_period(st.session_state.ledger)
        k1, k2, k3 = st.columns(3)
        k1.metric("Period Income", f"{inc:,.0f} CZK")
        k2.metric("Period Spend", f"{exp:,.0f} CZK", delta_color="inverse")
        k3.metric("Net Flow", f"{net:,.0f} CZK", delta=f"{net:,.0f}")
        visuals.render_trend_line(analytics.get_monthly_trend(st.session_state.ledger))
    else:
        st.info("Upload bank data to see cashflow trends.")

# 2. ASSETS
elif nav == "Assets & Liabilities":
    st.header("💎 Assets & Liabilities")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("assets_form"):
            st.subheader("Update Values")
            h = st.number_input("House", value=assets['house'])
            f = st.number_input("Fleet", value=assets['fleet'])
            m = st.number_input("Mortgage", value=assets['mortgage'])
            st.markdown("**Cash**")
            new_cash = {k: st.number_input(k, v) for k, v in assets['cash'].items()}
            if st.form_submit_button("Update"):
                st.session_state.assets = {'house': h, 'fleet': f, 'mortgage': m, 'cash': new_cash}
                st.rerun()
    with c2:
        visuals.render_t_form(assets['house'], assets['fleet'], stocks_val, assets['cash'], assets['mortgage'])

# 3. CASHFLOW & LEDGER (UPDATED)
elif nav == "Cashflow & Ledger":
    st.header("💸 Cashflow & Ledger")

    # --- TABBED INTERFACE FOR LEDGER TASKS ---
    l_tabs = st.tabs(["📂 Ingestion", "🛠️ Data Quality & Rules", "⚖️ Reconciliation", "📊 Reporting", "📜 Raw Data"])

    # A. Ingestion
    with l_tabs[0]:
        st.subheader("Upload Statements")
        files = st.file_uploader("CSV or ZIP", type=['csv', 'zip'], accept_multiple_files=True)
        if files:
            raw = []
            for name, obj in ingestion.process_uploaded_files(files):
                parsed = ingestion.parse_bank_file(obj, filename=name)
                if parsed is not None: raw.append(parsed)
            if raw:
                full = pd.concat(raw)
                st.session_state.ledger = processing.apply_categorization(full, st.session_state.rules)
                st.success(f"Processed {len(raw)} files.")
                st.rerun()

    # B. Data Quality (NEW)
    with l_tabs[1]:
        st.subheader("Data Quality Workbench")
        df = st.session_state.ledger
        if not df.empty:
            uncat = df[df['Category'] == 'Uncategorized']
            st.warning(f"⚠️ {len(uncat)} Uncategorized Transactions found.")

            c_rule, c_list = st.columns([1, 2])
            with c_rule:
                st.markdown("### Create Rule")
                r_pat = st.text_input("Pattern", placeholder="e.g. Starbucks")
                r_cat = st.selectbox("Category", ["Fixed", "Variable", "Invest", "Income", "Dining", "Transport"])
                if st.button("Add Rule & Re-Process"):
                    st.session_state.rules.append({'pattern': r_pat, 'target': r_cat})
                    st.session_state.ledger = processing.apply_categorization(df, st.session_state.rules)
                    st.success("Rule Applied!")
                    st.rerun()
            with c_list:
                st.markdown("### Uncategorized Items")
                st.dataframe(uncat[['Date', 'Description', 'Amount']], use_container_width=True)
        else:
            st.info("No data.")

    # C. Reconciliation (NEW)
    with l_tabs[2]:
        st.subheader("Balance Reconciliation")
        st.markdown("Verify your data integrity by checking the running balance against your bank statement.")

        c_set, c_chart = st.columns([1, 3])
        with c_set:
            check_date = st.date_input("Checkpoint Date", value=datetime.date.today())
            check_bal = st.number_input("Balance on Checkpoint Date", value=0.0)
            if st.button("Calculate Curve"):
                st.session_state.reconcile_params = (check_date, check_bal)

        with c_chart:
            if 'reconcile_params' in st.session_state and not st.session_state.ledger.empty:
                d, b = st.session_state.reconcile_params
                rec_df = analytics.calculate_running_balance(st.session_state.ledger, d, b)
                visuals.render_balance_history(rec_df)
                st.caption("If this curve matches your bank statement, your data is complete.")

    # D. Reporting
    with l_tabs[3]:
        if not st.session_state.ledger.empty:
            c1, c2 = st.columns(2)
            with c1: visuals.render_pie(analytics.get_expense_breakdown(st.session_state.ledger), 'AbsAmount',
                                        'Category', "Expenses")
            with c2: visuals.render_bar(analytics.get_fixed_vs_variable(st.session_state.ledger), 'Type', 'AbsAmount',
                                        "Fixed vs Variable", color='Type')

    # E. Raw Data
    with l_tabs[4]:
        if not st.session_state.ledger.empty and 'Date' in st.session_state.ledger.columns:
            st.dataframe(st.session_state.ledger.sort_values('Date', ascending=False), use_container_width=True)
        else:
            st.info("No transaction data available.")

# 4. PORTFOLIO
elif nav == "Investment Portfolio":
    st.header("📈 Investment Portfolio")

    with st.expander("Update Data"):
        pf = st.file_uploader("Upload CSV", type=['csv'])
        if pf:
            st.session_state.portfolio_metrics = portfolio.process_portfolio(pf)
            st.session_state.portfolio_source = "📂 Uploaded"
            st.rerun()

    if p_metrics:
        # 1. Key Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Value", f"{p_metrics['value']:,.0f} CZK")
        m2.metric("Total Profit", f"{p_metrics['profit']:,.0f} CZK",
                  delta=f"{(p_metrics['profit'] / p_metrics['cost'] * 100):.1f}%" if p_metrics['cost'] else None)
        m3.metric("Projected Annual Income", f"{p_metrics['divs_projected']:,.0f} CZK",
                  help="Based on Yield * Current Value")
        m4.metric("Portfolio Yield", f"{p_metrics['portfolio_yield']:.2f}%", help="Weighted Average")

        st.divider()

        # 2. Main Visuals (Sector + Winners)
        # Taking full width (internally splits to 2 columns)
        visuals.render_portfolio_visuals(p_metrics)

        st.markdown("<br>", unsafe_allow_html=True)

        # 3. Dividend Intelligence (New Row)
        st.subheader("Dividend Intelligence")
        # Placing in a container for cleaner alignment, though full width is fine
        visuals.render_dividend_comparison(p_metrics['divs_earned'], p_metrics['divs_projected'])

        st.divider()
        st.subheader("Holdings")
        st.dataframe(p_metrics['df'], use_container_width=True)
    else:
        st.warning("No portfolio data.")