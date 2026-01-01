import streamlit as st
from decimal import Decimal
from services.auth import AuthService
from services.ledger import LedgerService
from src.core.json_impl import JsonAssetRepository
from src.application.asset_service import AssetService
from src.domain.enums import AssetCategory


def render_view():
    st.title("🏛️ Assets & Liabilities")

    # Dependency Injection
    auth = AuthService()
    repo = JsonAssetRepository()
    service = AssetService(repo)

    # Legacy Service for the "Operating Cash" metric
    ls = LedgerService()
    ledger_df = ls.load_ledger()
    ledger_balance = ledger_df['Amount'].sum() if not ledger_df.empty else 0

    # 1. Data Loading
    assets = service.get_user_assets()

    # 2. Migration Check
    # If we have no new assets, but the old file exists, offer migration
    legacy_path = auth.get_file_path("assets.json")
    if not assets and legacy_path.exists():
        st.warning("⚠️ Legacy data found.")
        if st.button("Migrate to V2 Architecture"):
            if service.migrate_legacy_data(legacy_path):
                st.success("Migration complete! Please refresh.")
                st.rerun()
            else:
                st.error("Migration failed.")
        st.divider()

    # 3. KPI Header
    snapshot = service.get_net_worth_snapshot()
    # Add Ledger Balance to Total Cash for the KPI (Visual only)
    # Note: We don't save Ledger Balance as an Asset yet to avoid duplication
    adjusted_net_worth = snapshot.net_worth + Decimal(ledger_balance)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Net Worth", f"{adjusted_net_worth:,.0f} CZK")
    k2.metric("Hard Assets", f"{snapshot.total_assets:,.0f} CZK")
    k3.metric("Liabilities", f"{snapshot.total_liabilities:,.0f} CZK")
    k4.metric("Operating Cash (Ledger)", f"{ledger_balance:,.0f} CZK")

    st.divider()

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

                        # Edit Name
                        new_name = c_name.text_input(
                            "Name",
                            value=asset.name,
                            key=f"name_{asset.id}",
                            label_visibility="collapsed"
                        )

                        # Edit Value
                        new_val = c_val.number_input(
                            "Value",
                            value=float(asset.value),
                            key=f"val_{asset.id}",
                            step=1000.0,
                            label_visibility="collapsed"
                        )

                        # Save/Delete Actions
                        with c_btn:
                            if st.button("💾", key=f"save_{asset.id}", help="Save Changes"):
                                asset.name = new_name
                                service.update_asset_value(asset, Decimal(new_val))
                                st.toast(f"Updated {asset.name}")
                                st.rerun()

                            if st.button("🗑️", key=f"del_{asset.id}", help="Delete Asset"):
                                service.delete_asset(asset.id)
                                st.rerun()
            else:
                st.caption(f"No {category.value} assets found.")

            # --- Add New Asset ---
            st.divider()
            with st.expander(f"➕ Add New {category.value}"):
                with st.form(f"add_{category.name}"):
                    new_asset_name = st.text_input("Asset Name", placeholder="e.g. Summer House")
                    new_asset_val = st.number_input("Value", min_value=0.0, step=1000.0)

                    if st.form_submit_button("Create Asset"):
                        service.create_simple_asset(new_asset_name, category, Decimal(new_asset_val))
                        st.success("Asset Created!")
                        st.rerun()