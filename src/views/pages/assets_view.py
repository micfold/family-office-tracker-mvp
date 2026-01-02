# src/views/pages/assets_view.py
import streamlit as st
from decimal import Decimal
from src.container import get_container
from src.domain.enums import AssetCategory, LiabilityCategory, CashCategory, Currency
from src.views.components.kpi_cards import render_executive_summary_cards

# --- IMPORTS for components ---
from src.views.components.asset_cards import render_asset_card
from src.views.components.liability_cards import render_liability_card


def render_view():
    st.title("🏛️ Assets & Liabilities")

    container = get_container()
    asset_svc = container['asset']
    liab_svc = container['liability']
    summary_data = container['summary'].get_executive_summary()

    render_executive_summary_cards(summary_data)

    t_re, t_veh, t_cash, t_liab = st.tabs(["🏡 Real Estate", "🚗 Vehicles", "💰 Cash", "💳 Liabilities"])

    # --- 1. REAL ESTATE ---
    with t_re:
        assets = [a for a in asset_svc.get_user_assets() if a.category == AssetCategory.REAL_ESTATE]
        for a in assets:
            render_asset_card(a, asset_svc.update_asset_value, asset_svc.delete_asset, "🏡")

        st.divider()
        with st.expander("➕ Add Property"):
            _render_add_asset_form(asset_svc, AssetCategory.REAL_ESTATE)

    # --- 2. VEHICLES ---
    with t_veh:
        assets = [a for a in asset_svc.get_user_assets() if a.category == AssetCategory.VEHICLE]
        for a in assets:
            render_asset_card(a, asset_svc.update_asset_value, asset_svc.delete_asset, "🚗")

        st.divider()
        with st.expander("➕ Add Vehicle"):
            _render_add_asset_form(asset_svc, AssetCategory.VEHICLE)

    # --- 3. CASH ---
    with t_cash:
        assets = [a for a in asset_svc.get_user_assets() if a.category == AssetCategory.CASH]
        for a in assets:
            render_asset_card(a, asset_svc.update_asset_value, asset_svc.delete_asset, "💰")

        st.divider()
        with st.expander("➕ Add Cash Account"):
            _render_add_asset_form(asset_svc, AssetCategory.CASH)

    # --- 4. LIABILITIES ---
    with t_liab:
        liabs = liab_svc.get_user_liabilities()
        for l in liabs:
            render_liability_card(l, liab_svc.update_liability_details, liab_svc.delete_liability, "💳")

        st.divider()
        with st.expander("➕ Add Liability"):
            _render_add_liability_form(liab_svc)


def _render_add_asset_form(service, category):
    """
    Renders a unified form for adding assets, adapting fields based on category.
    """
    with st.form(f"add_{category.name}_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name")
        val = c2.number_input("Value / Amount", step=1000.0)

        kwargs = {}

        # Conditional Fields
        if category == AssetCategory.REAL_ESTATE:
            from src.views.components.address_autocomplete import render_address_input_with_autocomplete
            
            st.markdown("---")
            st.markdown("**📍 Property Location**")
            
            # Note: We can't use the autocomplete component inside a form
            # so we'll add a note and use a simpler approach
            c3, c4 = st.columns(2)
            kwargs['address'] = c3.text_input(
                "Address", 
                help="Enter the full address. After submitting, you can edit to use address autocomplete."
            )
            kwargs['area_m2'] = Decimal(c4.number_input("Area (m²)", step=1.0))

        elif category == AssetCategory.VEHICLE:
            st.markdown("---")
            c3, c4 = st.columns(2)
            kwargs['brand'] = c3.text_input("Brand")
            kwargs['model'] = c4.text_input("Model")
            kwargs['insurance_cost'] = Decimal(st.number_input("Annual Insurance", step=100.0))

        elif category == AssetCategory.CASH:
            st.markdown("---")
            kwargs['cash_type'] = st.selectbox("Type", [t.value for t in CashCategory])
            kwargs['bucket_name'] = st.text_input("Envelope / Bucket Name")
            kwargs['currency'] = st.selectbox("Currency", [c.value for c in Currency])

            c3, c4 = st.columns(2)
            kwargs['account_number'] = c3.text_input("Account Number")
            kwargs['bank_code'] = c4.text_input("Bank Code")

        if st.form_submit_button("Add Asset", type="primary"):
            service.create_asset(name, category, Decimal(val), **kwargs)
            st.rerun()


def _render_add_liability_form(service):
    with st.form("add_liab_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Name (e.g. Mortgage)")
        l_type = c2.selectbox("Type", [t.value for t in LiabilityCategory])

        inst = st.text_input("Institution / Lender", placeholder="e.g. Chase Bank")

        c3, c4 = st.columns(2)
        amt = c3.number_input("Outstanding Balance", step=10000.0)
        rate = c4.number_input("Interest Rate (%)", step=0.1)

        if st.form_submit_button("Add Liability", type="primary"):
            service.create_liability(
                name,
                Decimal(amt),
                l_type,
                institution=inst,
                interest_rate=Decimal(rate)
            )
            st.rerun()