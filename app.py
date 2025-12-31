# app.py
import streamlit as st
import pandas as pd
import os
import datetime
from config.settings import GLOBAL_RULES, DEFAULT_PORTFOLIO_FILE, DEFAULT_HISTORY_FILE, UI_CATEGORIES
from modules import ingestion, processing, analytics, portfolio
from components import visuals

st.set_page_config(page_title="Family Office HQ", layout="wide", page_icon="🏛️")

# --- INITIALIZATION ---
if 'user_rules' not in st.session_state: st.session_state.user_rules = []
if 'ledger' not in st.session_state: st.session_state.ledger = pd.DataFrame()
# NEW: Track processed files to prevent duplicates
if 'processed_files' not in st.session_state: st.session_state.processed_files = set()

if 'assets' not in st.session_state:
    st.session_state.assets = {
        'house': 18320000, 'fleet': 1500000, 'mortgage': 13000000,
        'cash': {'Emergency': 400000, 'Fleet': 100000, 'Living': 99000}
    }

# --- UNIFIED PORTFOLIO STATE ---
if 'portfolio_data' not in st.session_state:
    st.session_state.portfolio_data = {'snapshot': None, 'history': None}


@st.cache_data
def load_port_file(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return portfolio.process_portfolio(f)
    return None


# Auto-load defaults on boot
if st.session_state.portfolio_data['snapshot'] is None:
    st.session_state.portfolio_data['snapshot'] = load_port_file(DEFAULT_PORTFOLIO_FILE)

if st.session_state.portfolio_data['history'] is None:
    st.session_state.portfolio_data['history'] = load_port_file(DEFAULT_HISTORY_FILE)


# Helper to get current Total Value (Snapshot Preferred, else History Proxy)
def get_portfolio_value():
    s = st.session_state.portfolio_data['snapshot']
    h = st.session_state.portfolio_data['history']
    if s: return s['value']
    if h: return h['value_proxy']
    return 0.0


# --- GLOBALS ---
stocks_val = get_portfolio_value()
assets = st.session_state.assets
total_cash = sum(assets['cash'].values())
total_assets = assets['house'] + assets['fleet'] + stocks_val + total_cash
net_worth = total_assets - assets['mortgage']

# Navigation State
if 'nav_selection' not in st.session_state: st.session_state.nav_selection = "Dashboard Overview"
if 'pending_nav' in st.session_state:
    st.session_state.nav_selection = st.session_state.pending_nav
    del st.session_state.pending_nav


def go_to_page(p): st.session_state.pending_nav = p


# --- SIDEBAR ---
with st.sidebar:
    st.title("🏛️ Control Tower")
    st.radio(
        "Navigate to:",
        ["Dashboard Overview", "Assets & Liabilities", "Cashflow & Ledger", "Investment Portfolio"],
        key="nav_selection"
    )
    st.divider()

    # Portfolio Status
    s_ok = st.session_state.portfolio_data['snapshot'] is not None
    h_ok = st.session_state.portfolio_data['history'] is not None

    if s_ok or h_ok:
        st.success(f"Portfolio: {'Snapshot' if s_ok else ''} {'+ History' if h_ok else ''}")
    else:
        st.warning("Portfolio: Empty")

    if not st.session_state.ledger.empty:
        st.success(f"Ledger: {len(st.session_state.ledger)} Tx")

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

    l_tabs = st.tabs(["📂 Ingestion", "🛠️ Data Quality", "⚖️ Reconciliation", "📊 Reporting", "📜 Data"])

    # A. Ingestion
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
                    new_files_count = 0

                    # Logic to prevent duplicate uploads
                    for name, obj in ingestion.process_uploaded_files(files):
                        if name in st.session_state.processed_files:
                            st.warning(f"⚠️ Skipped '{name}': Already processed.")
                            continue

                        parsed = ingestion.parse_bank_file(obj, filename=name)
                        if parsed is not None:
                            raw.append(parsed)
                            st.session_state.processed_files.add(name)
                            new_files_count += 1

                    if raw:
                        full = pd.concat(raw)
                        # Merge with existing ledger
                        if not st.session_state.ledger.empty:
                            full = pd.concat([st.session_state.ledger, full]).drop_duplicates()

                        st.session_state.ledger = processing.apply_categorization(
                            full, GLOBAL_RULES, st.session_state.user_rules
                        )
                        st.success(f"✅ Successfully processed {new_files_count} new files!")
                        st.rerun()
                    elif new_files_count == 0:
                        st.info("ℹ️ No new files to process.")

        # 2. Manual Entry
        with col_manual:
            st.subheader("Manual Entry")
            st.caption("Add single cash transactions.")

            # --- 1. Type Selector (OUTSIDE Form -> Allows Refresh) ---
            sel_type = st.selectbox("Transaction Type", list(UI_CATEGORIES.keys()), key="man_type_sel")

            # --- 2. The Form (INSIDE -> Prevents Lag/Buggy clicks) ---
            with st.form("manual_entry_form"):
                d_date = st.date_input("Date", datetime.date.today())
                d_desc = st.text_input("Description", placeholder="e.g. Taxi payment")

                c_amt, c_curr = st.columns([2, 1])
                d_amt = c_amt.number_input("Amount", value=0.0, step=100.0, help="- for expense, + for income")
                d_curr = c_curr.selectbox("Currency", ["🇨🇿 CZK", "🇪🇺 EUR", "🇺🇸 USD", "🇬🇧 GBP", "🇨🇭 CHF", "🇯🇵 JPY"])

                # Category (Updates based on sel_type outside)
                sel_cat = st.selectbox("Category", UI_CATEGORIES[sel_type])

                if st.form_submit_button("Add Transaction"):
                    new_row = pd.DataFrame([{
                        'Date': pd.to_datetime(d_date), 'Description': d_desc,
                        'Amount': d_amt, 'Currency': d_curr, 'Source': 'Manual Entry',
                        'Category': sel_cat
                    }])

                    if not st.session_state.ledger.empty:
                        updated_df = pd.concat([st.session_state.ledger, new_row], ignore_index=True)
                    else:
                        updated_df = new_row

                    st.session_state.ledger = processing.apply_categorization(updated_df, GLOBAL_RULES,
                                                                              st.session_state.user_rules)
                    st.success("Transaction added!")
                    st.rerun()
    # B. Data Quality
    with l_tabs[1]:
        st.subheader("Data Quality Workbench")
        df = st.session_state.ledger

        if not df.empty:
            # Smart Suggestions
            sug = processing.suggest_patterns(df)
            if not sug.empty:
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.markdown("#### Smart Suggestions")
                    st.dataframe(sug[['Description', 'Count', 'Total_Value', 'Example_Currency']],
                                 width='stretch', selection_mode="single-row", on_select="rerun",
                                 key="suggestion_table")
                with c2:
                    st.markdown("#### Quick Rule Creator")
                    if "suggestion_table" in st.session_state and st.session_state.suggestion_table.selection.rows:
                        row_idx = st.session_state.suggestion_table.selection.rows[0]
                        sel_desc = sug.iloc[row_idx]['Description']

                        st.write(f"**Pattern:** `{sel_desc}`")

                        # --- 1. Type (Outside) ---
                        qr_type = st.selectbox("Rule Type", list(UI_CATEGORIES.keys()), key="qr_type_sel")

                        # --- 2. Form (Inside) ---
                        with st.form("quick_rule_form"):
                            qr_cat = st.selectbox("Category", UI_CATEGORIES[qr_type])

                            if st.form_submit_button("Create Rule"):
                                st.session_state.user_rules.append({'pattern': sel_desc, 'target': qr_cat})
                                st.session_state.ledger = processing.apply_categorization(
                                    st.session_state.ledger, GLOBAL_RULES, st.session_state.user_rules
                                )
                                st.success("Rule applied!")
                                st.rerun()
                    else:
                        st.info("👈 Select a suggestion.")
            else:
                st.success("All patterns handled!")

            st.divider()
            uncat = df[df['Category'] == 'Uncategorized']
            st.markdown(f"#### Uncategorized Items ({len(uncat)})")
            st.dataframe(uncat[['Date', 'Description', 'Amount', 'Currency', 'Source']], width='stretch')
        else:
            st.info("No data loaded.")

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
            st.info("No data available.")

    # E. Raw Data
    with l_tabs[4]:
        if not st.session_state.ledger.empty:
            st.dataframe(st.session_state.ledger.sort_values('Date', ascending=False), width='stretch')
        else:
            st.info("No data available.")

# 4. PORTFOLIO
elif nav == "Investment Portfolio":
    st.header("📈 Investment Portfolio")

    with st.expander("Update Portfolio Data"):
        pf = st.file_uploader("Upload Snapshot OR History CSV", type=['csv'])
        if pf:
            res = portfolio.process_portfolio(pf)
            if res:
                # Intelligently update the correct slot based on file content
                ptype = res['type']
                st.session_state.portfolio_data[ptype] = res
                st.success(f"Updated {ptype.title()} Data!")
                st.rerun()
            else:
                st.error("Could not process file.")

    snap = st.session_state.portfolio_data['snapshot']
    hist = st.session_state.portfolio_data['history']

    if snap or hist:
        # Call the unified renderer from components/visuals.py
        visuals.render_unified_portfolio(snap, hist)
    else:
        c_info, c_btn = st.columns([3, 1])
        with c_info:
            st.warning("No portfolio data found.")
        with c_btn:
            st.info("⬆️ Use the uploader above.")

