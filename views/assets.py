# views/assets.py
import streamlit as st
import json
from services.auth import AuthService


def render_view():
    st.title("💎 Assets & Liabilities")

    auth = AuthService()
    file_path = auth.get_file_path("assets.json")

    # Load existing or default
    if file_path.exists():
        with open(file_path, 'r') as f:
            assets = json.load(f)
    else:
        assets = {"Real Estate": 0, "Vehicles": 0, "Mortgage": 0}

    # Form
    with st.form("asset_update"):
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Assets")
            re_val = st.number_input("Real Estate Value", value=assets.get("Real Estate", 0))
            veh_val = st.number_input("Vehicles Value", value=assets.get("Vehicles", 0))

        with c2:
            st.subheader("Liabilities")
            mort_val = st.number_input("Mortgage Balance", value=assets.get("Mortgage", 0))

        if st.form_submit_button("Update Balance Sheet"):
            new_data = {
                "Real Estate": re_val,
                "Vehicles": veh_val,
                "Mortgage": mort_val
            }
            with open(file_path, 'w') as f:
                json.dump(new_data, f)
            st.success("Assets updated!")
            st.rerun()

    # Simple Visual
    net_worth = (assets.get("Real Estate", 0) + assets.get("Vehicles", 0)) - assets.get("Mortgage", 0)
    st.metric("Net Worth (Excl. Portfolio)", f"{net_worth:,.0f} CZK")