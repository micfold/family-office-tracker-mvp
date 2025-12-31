# app.py
import streamlit as st
import pandas as pd
import os
import datetime
from config.settings import GLOBAL_RULES, DEFAULT_PORTFOLIO_FILE
from modules import ingestion, processing, analytics, portfolio
from components import visuals

st.set_page_config(page_title="Family Office HQ", layout="wide", page_icon="🏛️")

# --- INITIALIZATION ---
if 'user_rules' not in st.session_state: st.session_state.user_rules = []
if 'ledger' not in st.session_state: st.session_state.ledger = pd.DataFrame()
if 'assets' not in st.session_state:
    st.session_state.assets = {
        'house': 18320000, 'fleet': 1500000, 'mortgage': 13000000,
        'cash': {'Emergency': 400000, 'Fleet Sinking': 100000, 'Living': 99000}
    }

# Navigation State (Required for Deep Linking)
if 'nav_selection' not in st.session_state:
    st.session_state.nav_selection = "Dashboard Overview"

# Check for pending navigation (set by button callbacks)
if 'pending_nav' in st.session_state:
    st.session_state.nav_selection = st.session_state.pending_nav
    del st.session_state.pending_nav


# Helper for Deep Linking (uses callback pattern)
def go_to_page(page_name):
    st.session_state.pending_nav = page_name


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

    # Navigation with Key for State Sync
    # We use the key 'nav_selection' so modifying st.session_state.nav_selection updates this widget
    st.radio(
        "Navigate to:",
        ["Dashboard Overview", "Assets & Liabilities", "Cashflow & Ledger", "Investment Portfolio"],
        key="nav_selection"
    )

    st.divider()
    if st.session_state.portfolio_metrics: st.success(f"Portfolio: {st.session_state.portfolio_source}")
    if not st.session_state.ledger.empty: st.success(f"Ledger: {len(st.session_state.ledger)} Tx")

# --- VIEWS ---
nav = st.session_state.nav_selection

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
        # CTA for Missing Data (Deep Link)
        c_info, c_btn = st.columns([3, 1])
        with c_info:
            st.info("💡 No cashflow data loaded. Upload statements to see trends.")
        with c_btn:
            st.button("🚀 Upload Bank Statements", width='stretch',
                     on_click=go_to_page, args=("Cashflow & Ledger",))

# 2. ASSETS
elif nav == "Assets & Liabilities":
    st.header("💎 Assets & Liabilities")
    c1, c2 = st.columns([1, 2])
    with c1:
        with st.form("assets"):
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

# 3. CASHFLOW & LEDGER
elif nav == "Cashflow & Ledger":
    st.header("💸 Cashflow & Ledger")

    l_tabs = st.tabs(["📂 Ingestion", "🛠️ Data Quality & Rules", "⚖️ Reconciliation", "📊 Reporting", "📜 Raw Data"])

    # A. Ingestion (Bulk + Manual)
    with l_tabs[0]:
        col_file, col_manual = st.columns([1, 1], gap="large")

        # 1. Bulk Upload
        with col_file:
            st.subheader("Statement Upload")
            st.caption("Supports CSV and ZIP archives.")
            files = st.file_uploader("Drop files here", type=['csv', 'zip'], accept_multiple_files=True)
            if files:
                if st.button("📥 Process Files", type="secondary", width='stretch'):
                    raw = []
                    for name, obj in ingestion.process_uploaded_files(files):
                        parsed = ingestion.parse_bank_file(obj, filename=name)
                        if parsed is not None: raw.append(parsed)
                    if raw:
                        full = pd.concat(raw)
                        # Merge with existing ledger if needed
                        if not st.session_state.ledger.empty:
                            full = pd.concat([st.session_state.ledger, full]).drop_duplicates()

                        st.session_state.ledger = processing.apply_categorization(
                            full, GLOBAL_RULES, st.session_state.user_rules
                        )
                        st.success(f"Processed {len(raw)} files successfully!")
                        st.rerun()

        # 2. Manual Entry
        with col_manual:
            st.subheader("Manual Entry")
            st.caption("Add single cash transactions.")
            with st.form("manual_entry"):
                d_date = st.date_input("Date", datetime.date.today())
                d_desc = st.text_input("Description", placeholder="e.g. Taxi payment")
                c_amt, c_curr = st.columns([2, 1])
                d_amt = c_amt.number_input("Amount", value=0.0, step=100.0,
                                           help="Negative for expense, Positive for income")
                d_curr = c_curr.selectbox("Currency", ["🇨🇿 CZK", "🇪🇺 EUR", "🇺🇸 USD", "🇬🇧 GBP", "🇨🇭 CHF", "🇯🇵 JPY"])

                if st.form_submit_button("Add Transaction"):
                    new_row = pd.DataFrame([{
                        'Date': pd.to_datetime(d_date),
                        'Description': d_desc,
                        'Amount': d_amt,
                        'Currency': d_curr,
                        'Source': 'Manual Entry'
                    }])

                    # Append to ledger
                    current_df = st.session_state.ledger
                    updated_df = pd.concat([current_df, new_row], ignore_index=True)

                    # Auto-Categorize this new entry immediately
                    st.session_state.ledger = processing.apply_categorization(
                        updated_df, GLOBAL_RULES, st.session_state.user_rules
                    )
                    st.success("Transaction added!")
                    st.rerun()

    # B. Data Quality
    with l_tabs[1]:
        st.subheader("Data Quality Workbench")
        df = st.session_state.ledger

        if not df.empty:
            uncat = df[df['Category'] == 'Uncategorized']

            # Smart Suggestions
            st.markdown("#### 1. Smart Suggestions")
            st.caption("We grouped similar transactions. Create one rule to fix many records.")

            suggestions = processing.suggest_patterns(df)

            if not suggestions.empty:
                col_s1, col_s2 = st.columns([2, 1])
                with col_s1:
                    st.dataframe(
                        suggestions[['Description', 'Count', 'Total_Value', 'Example_Currency']],
                        width='stretch',
                        selection_mode="single-row",
                        on_select="rerun",
                        key="suggestion_table"
                    )
                with col_s2:
                    st.markdown("##### Quick Rule Creator")
                    # Check selection
                    if "suggestion_table" in st.session_state and st.session_state.suggestion_table.selection.rows:
                        row_idx = st.session_state.suggestion_table.selection.rows[0]
                        sel_desc = suggestions.iloc[row_idx]['Description']

                        with st.form("quick_rule"):
                            st.write(f"**Pattern:** `{sel_desc}`")
                            r_cat = st.selectbox("Assign Category",
                                                 ["Fixed", "Variable", "Invest", "Income", "Dining", "Transport",
                                                  "Health"])
                            if st.form_submit_button("Create Rule"):
                                st.session_state.user_rules.append({'pattern': sel_desc, 'target': r_cat})
                                st.session_state.ledger = processing.apply_categorization(
                                    st.session_state.ledger, GLOBAL_RULES, st.session_state.user_rules
                                )
                                st.success("Rule applied!")
                                st.rerun()
                    else:
                        st.info("👈 Select a row to create a rule.")
            else:
                st.success("🎉 No uncategorized patterns found!")

            st.divider()
            st.markdown("#### 2. Detailed Uncategorized List")
            st.dataframe(uncat[['Date', 'Description', 'Amount', 'Currency', 'Source']], width='stretch')
        else:
            st.info("📂 No data loaded. Use the **📂 Ingestion** tab above to upload bank statements or add manual transactions.")

    # C. Reconciliation
    with l_tabs[2]:
        st.subheader("Balance Reconciliation")
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

    # D. Reporting
    with l_tabs[3]:
        if not st.session_state.ledger.empty:
            c1, c2 = st.columns(2)
            with c1:
                visuals.render_pie(analytics.get_expense_breakdown(st.session_state.ledger), 'AbsAmount', 'Category',
                                   "Expenses")
            with c2:
                visuals.render_bar(analytics.get_fixed_vs_variable(st.session_state.ledger), 'Type', 'AbsAmount',
                                   "Fixed vs Variable", color='Type')
        else:
            st.info("📂 No data loaded. Use the **📂 Ingestion** tab above to upload bank statements or add manual transactions.")

    # E. Raw Data
    with l_tabs[4]:
        if not st.session_state.ledger.empty:
            st.dataframe(st.session_state.ledger.sort_values('Date', ascending=False), width='stretch')
        else:
            st.info("📂 No data loaded. Use the **📂 Ingestion** tab above to upload bank statements or add manual transactions.")

# 4. PORTFOLIO
elif nav == "Investment Portfolio":
    st.header("📈 Investment Portfolio")

    with st.expander("Update Data"):
        pf = st.file_uploader("Upload CSV (Holdings or History)", type=['csv'])
        if pf:
            # Process and determine type automatically
            metrics = portfolio.process_portfolio(pf)
            if metrics:
                st.session_state.portfolio_metrics = metrics
                st.session_state.portfolio_source = f"📂 {pf.name}"
                st.rerun()

    if p_metrics:
        # CHECK TYPE: SNAPSHOT vs HISTORY
        p_type = p_metrics.get('type', 'snapshot')

        if p_type == 'snapshot':
            # -- RENDER HOLDINGS DASHBOARD --
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Value", f"{p_metrics['value']:,.0f} CZK")
            m2.metric("Total Profit", f"{p_metrics['profit']:,.0f} CZK",
                      delta=f"{(p_metrics['profit'] / p_metrics['cost'] * 100):.1f}%" if p_metrics['cost'] else None)
            m3.metric("Projected Annual Divs", f"{p_metrics['divs_projected']:,.0f} CZK")
            m4.metric("Portfolio Yield", f"{p_metrics['portfolio_yield']:.2f}%")

            st.divider()
            visuals.render_portfolio_visuals(p_metrics)

            st.subheader("Dividend Intelligence")
            visuals.render_dividend_comparison(p_metrics['divs_earned'], p_metrics['divs_projected'])

            st.dataframe(p_metrics['df'], width='stretch')

        elif p_type == 'history':
            # -- RENDER HISTORY DASHBOARD --
            st.info("🕒 History Mode: Showing Invested Capital & Dividend Trends over time.")
            visuals.render_portfolio_visuals(p_metrics)

            with st.expander("Raw Transaction Ledger"):
                st.dataframe(p_metrics['raw'], width='stretch')

    else:
        c_info, c_btn = st.columns([3, 1])
        with c_info:
            st.warning("No portfolio data.")
        with c_btn:
            st.info("⬆️ Use the uploader above.")