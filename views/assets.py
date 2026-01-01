# views/assets.py
import streamlit as st
from services.assets import AssetsService  # <--- Use Service
from services.ledger import LedgerService
from services.portfolio import PortfolioService
from components import visuals


def render_view():
    st.title("💎 Assets & Liabilities")

    # Initialize Services
    as_svc = AssetsService()
    ps = PortfolioService()
    ls = LedgerService()

    # Load Data
    assets = as_svc.load_assets()
    port_data = ps.load_data()
    ledger_df = ls.load_ledger()

    portfolio_val = 0
    if port_data.get('snapshot'):
        portfolio_val = port_data['snapshot']['value']
    elif port_data.get('history'):
        portfolio_val = port_data['history']['value_proxy']

    ledger_balance = 0.0
    if not ledger_df.empty:
        ledger_balance = ledger_df['Amount'].sum()

        # --- INPUT FORM (Manual Assets Only) ---
        with st.form("asset_update"):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.subheader("🏡 Hard Assets")
                re_val = st.number_input("Real Estate", value=assets.get("Real Estate", 0))
                veh_val = st.number_input("Vehicles", value=assets.get("Vehicles", 0))

            with c2:
                st.subheader("💵 Cash Positions")
                # Display Ledger Balance as Read-Only
                st.metric("🏦 Operating Accounts (Ledger)", f"{ledger_balance:,.0f} CZK",
                          help="Auto-calculated from Cashflow & Ledger")

                st.divider()
                st.caption("Manual Cash Entries")

                # Dynamic fields for manual cash (Emergency, Wallet, etc.)
                cash_dict = assets.get("Cash", {})
                new_cash_dict = {}
                for k, v in cash_dict.items():
                    new_cash_dict[k] = st.number_input(f"{k}", value=v)

            with c3:
                st.subheader("🏦 Liabilities")
                mort_val = st.number_input("Mortgage", value=assets.get("Mortgage", 0))

            if st.form_submit_button("Update Balance Sheet"):
                new_data = {
                    "Real Estate": re_val,
                    "Vehicles": veh_val,
                    "Mortgage": mort_val,
                    "Cash": new_cash_dict
                }
                as_svc.save_assets(new_data)
                st.success("Assets updated!")
                st.rerun()

        # --- VISUALIZATION ---
        # Combine Manual Cash + Ledger Balance for the Chart
        display_cash = assets.get("Cash", {}).copy()
        display_cash["Operating Accounts (Ledger)"] = ledger_balance

        visuals.render_t_form(
            assets.get("Real Estate", 0),
            assets.get("Vehicles", 0),
            portfolio_val,
            display_cash,  # <--- Now includes Ledger Balance
            assets.get("Mortgage", 0)
        )