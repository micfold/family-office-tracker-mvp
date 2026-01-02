# src/views/pages/assets_view.py
import streamlit as st
from decimal import Decimal
from src.container import get_container
from src.domain.enums import AssetCategory, LiabilityCategory, CashCategory, Currency, RealEstateType
from src.views.components.kpi_cards import render_executive_summary_cards
from src.views.utils import format_currency, get_currency_icon

# --- IMPORTS for components ---
from src.views.components.asset_cards import render_asset_card
from src.views.components.liability_cards import render_liability_card
from src.views.components.numeric_input import render_numeric_input
from src.views.utils import identify_bank, get_address_suggestions, get_place_details


def render_view():
    st.title("🏛️ Assets & Liabilities")

    with st.spinner("Loading..."):
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
        if st.button("Update Vehicle Market Values", key="update_vehicle_values"):
            asset_svc.run_vehicle_amortization_update()
            st.toast("Vehicle values updated based on amortization.", icon="🎉")
            st.rerun()

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


def _get_state(category_name: str):
    """Initializes and returns the state for a given asset category."""
    state_key = f"add_asset_form_{category_name}"
    if state_key not in st.session_state:
        st.session_state[state_key] = {
            'val': 0.0, 'currency': Currency.USD.value, 'property_type': RealEstateType.PRIMARY_RESIDENCE.value,
            'address': '', 'city': '', 'postal_code': '', 'area_m2': 0.0, 'annual_cost_projection': 0.0,
            'brand': '', 'model': '', 'year_made': 2026, 'kilometers_driven': 0, 'color': '#FFFFFF',
            'insurance_cost': 0.0, 'cash_type': CashCategory.CHECKING_ACCOUNT.value, 'bucket_name': '',
            'account_identifier': ''
        }
    return st.session_state[state_key]


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
    """Renders the form for adding liabilities without using st.form."""
    state_key = "add_liability_form"
    if state_key not in st.session_state:
        st.session_state[state_key] = {
            'inst': '', 'l_type': LiabilityCategory.MORTGAGE.value, 'amt': 0.0,
            'currency': Currency.USD.value, 'rate': 0.0, 'has_insurance': False, 'insurance_cost': 0.0
        }
    state = st.session_state[state_key]

    c1, c2 = st.columns(2)
    state['inst'] = c1.text_input("Institution / Lender", placeholder="e.g. Chase Bank", value=state['inst'])
    state['l_type'] = c2.selectbox("Type", options=LiabilityCategory, format_func=lambda t: t.value)

    c3, c4 = st.columns(2)
    with c3:
        state['amt'] = render_numeric_input("Outstanding Balance", key="add_liab_amt")
    with c4:
        state['currency'] = st.selectbox(
            "Currency",
            [c.value for c in Currency],
            format_func=lambda x: f"{get_currency_icon(x)} {x}",
            key="add_liability_currency"
        )

    c5, c6 = st.columns(2)
    state['rate'] = c5.number_input("Interest Rate (%)", step=0.1, format="%.2f", value=state['rate'])
    state['has_insurance'] = c6.checkbox("Has Insurance", value=state['has_insurance'])

    if state['has_insurance']:
        state['insurance_cost'] = render_numeric_input("Annual Insurance Cost", key="add_liab_insurance")

    # --- Mortgage-Specific Fields ---
    if state['l_type'] == LiabilityCategory.MORTGAGE.value:
        st.markdown("---")
        st.subheader("Mortgage Details")
        c7, c8 = st.columns(2)
        state['start_date'] = c7.date_input("Mortgage Start Date")
        state['annual_interest_paid'] = c8.number_input("Annual Interest Paid", step=1000.0)

    if st.button("Add Liability", type="primary", key="add_liability_btn"):
        service.create_liability(
            amount=state['amt'], currency=state['currency'], liability_type=state['l_type'],
            institution=state['inst'], interest_rate=Decimal(state['rate']),
            has_insurance=state['has_insurance'],
            insurance_cost=state['insurance_cost'] if state['has_insurance'] else None,
            start_date=state.get('start_date'),
            annual_interest_paid=Decimal(state.get('annual_interest_paid', 0))
        )
        del st.session_state[state_key]
        st.rerun()
