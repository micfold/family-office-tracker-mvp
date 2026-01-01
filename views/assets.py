# views/assets.py
import streamlit as st
import json
from services.auth import AuthService
from components import visuals
from services.portfolio import PortfolioService


def render_view():
    st.title("💎 Assets & Liabilities")

    auth = AuthService()

    ps = PortfolioService()
    port_data = ps.load_data()

    # Calculate Portfolio Value
    portfolio_val = 0
    if port_data.get('snapshot') is not None:
        portfolio_val = port_data['snapshot']['value']
    elif port_data.get('history') is not None:
        portfolio_val = port_data['history'].get('value_proxy', 0)

    file_path = auth.get_file_path("assets.json")

    # Load existing or default
    defaults = {
        "Real Estate": 0, "Vehicles": 0, "Mortgage": 0,
        "Cash": {"Emergency": 0, "Wallet": 0, "Savings": 0}
    }

    assets = defaults
    if file_path.exists():
        with open(file_path, 'r') as f:
            loaded = json.load(f)
            assets.update(loaded)

    # Input Form
    with st.form("asset_update"):
        c1, c2, c3 = st.columns(3)

        with c1:
            st.subheader("🏡 Hard Assets")
            re_val = st.number_input("Real Estate", value=assets.get("Real Estate", 0))
            veh_val = st.number_input("Vehicles", value=assets.get("Vehicles", 0))

        with c2:
            st.subheader("💵 Cash Positions")
            # Dynamic Cash Fields
            cash_dict = assets.get("Cash", defaults["Cash"])
            new_cash_dict = {}
            for k, v in cash_dict.items():
                new_cash_dict[k] = st.number_input(f"Cash: {k}", value=v)

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
            with open(file_path, 'w') as f:
                json.dump(new_data, f)
            st.success("Assets updated!")
            st.rerun()

    # Visuals
    # Re-use the nice Balance Sheet visual from Master
    visuals.render_t_form(
        assets.get("Real Estate", 0),
        assets.get("Vehicles", 0),
        0,  # Portfolio value should ideally be fetched from PortfolioService here
        assets.get("Cash", {}),
        assets.get("Mortgage", 0)
    )