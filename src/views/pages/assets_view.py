import streamlit as st
from decimal import Decimal
from src.container import get_container
from src.domain.enums import AssetCategory
from src.views.components.kpi_cards import render_executive_summary_cards

def render_view():
    st.title("🏛️ Assets & Liabilities")

    # 1. Get Services
    container = get_container()
    service = container['asset']
    # We grab the Summary service just for the Top-Level KPI consistency
    summary_data = container['summary'].get_executive_summary()

    # 2. Operations
    assets = service.get_user_assets()

    # 3. KPI Header (Now uses the consistent Summary Service)
    render_executive_summary_cards(summary_data)

    # 4. Asset Management Interface
    # We group assets by category into Tabs
    cat_order = [
        AssetCategory.REAL_ESTATE,
        AssetCategory.VEHICLE,
        AssetCategory.CASH,
        AssetCategory.EQUITY,
    ]

    tabs = st.tabs([c.value for c in cat_order])

    for i, category in enumerate(cat_order):
        with tabs[i]:
            # Filter assets for this tab
            current_cat_assets = [a for a in assets if a.category == category]

            # --- List Existing Assets ---
            if current_cat_assets:
                for asset in current_cat_assets:
                    with st.container(border=True):
                        c_name, c_val, c_btn = st.columns([3, 2, 1])
                        new_name = c_name.text_input("Name", value=asset.name, key=f"name_{asset.id}",
                                                     label_visibility="collapsed")
                        new_val = c_val.number_input("Value", value=float(asset.value), key=f"val_{asset.id}",
                                                     step=1000.0, label_visibility="collapsed")

                        # Save/Delete Actions
                        with c_btn:
                            if st.button("💾", key=f"save_{asset.id}"):
                                asset.name = new_name
                                service.update_asset_value(asset, Decimal(new_val))
                                st.toast("Saved")
                                st.rerun()
                            if st.button("🗑️", key=f"del_{asset.id}"):
                                service.delete_asset(asset.id)
                                st.rerun()
            st.divider()

            # --- Add New Asset ---
            st.divider()
            with st.expander(f"➕ Add New {category.value}"):
                with st.form(f"add_{category.name}"):
                    n_name = st.text_input("Name")
                    n_val = st.number_input("Value")
                    if st.form_submit_button("Create"):
                        service.create_simple_asset(n_name, category, Decimal(n_val))
                        st.rerun()