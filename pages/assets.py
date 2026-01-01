# views/assets.py
import streamlit as st
from services.assets import AssetsService
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
    re_data = assets.get("Real Estate", {})
    if isinstance(re_data, dict):
        prop_val = sum(re_data.values())
    else:
        prop_val = re_data
    port_data = ps.load_data()
    ledger_df = ls.load_ledger()

    portfolio_val = 0
    if port_data.get('snapshot'):
        portfolio_val = port_data['snapshot']['value']
    elif port_data.get('history'):
        portfolio_val = port_data['history']['value_proxy']

    if not ledger_df.empty:
        ledger_balance = ledger_df['Amount'].sum()

        if not isinstance(re_data, dict):
            re_data = {"Property & Land": re_data, "Interior & Decor": 0, "Appliances & Tech": 0}

        # --- INPUT FORM (Manual Assets Only) ---
        with st.form("asset_update"):
            c1, c2, c3 = st.columns(3)

            with c1:
                st.subheader("🏡 Hard Assets")
                prop_val = st.number_input("Property + Land", value=re_data.get("Property & Land", 0))
                decor_val = st.number_input("Interior & Decor", value=re_data.get("Interior & Decor", 0))
                app_val = st.number_input("Appliances & Tech", value=re_data.get("Appliances & Tech", 0))

                total_re = prop_val + decor_val + app_val
                st.info(f"Total Value: {total_re:,.0f} CZK")

                veh_val = st.number_input("Vehicles", value=assets.get("Vehicles", 0))

            with c2:
                st.subheader("💵 Cash Positions")

                st.metric("🏦 Operating Accounts (Ledger)", f"{ledger_balance:,.0f} CZK",
                          help="Auto-calculated from Cashflow & Ledger")
                st.divider()

                st.caption("Manual Cash Entries")
                cash_dict = assets.get("Cash", {})
                new_cash_dict = {}
                for k, v in cash_dict.items():
                    new_cash_dict[k] = st.number_input(f"{k}", value=v)

            with c3:
                st.subheader("🏦 Liabilities")
                mort_val = st.number_input("Mortgage", value=assets.get("Mortgage", 0))

            if st.form_submit_button("Update Balance Sheet"):

                new_data = {
                    "Real Estate": {
                    "Property & Land": prop_val,
                    "Interior & Decor": decor_val,
                    "Appliances & Tech": app_val
                },
                    "Vehicles": veh_val,
                    "Mortgage": mort_val,
                    "Cash": new_cash_dict
                }
                as_svc.save_assets(new_data)
                st.success("Assets updated!")
                st.rerun()

        # --- VISUALIZATION ---
        display_cash = assets.get("Cash", {}).copy()
        display_cash["Operating Accounts (Ledger)"] = ledger_balance

        visuals.render_t_form(
            prop_val,
            assets.get("Vehicles", 0),
            portfolio_val,
            display_cash,
            assets.get("Mortgage", 0)
        )