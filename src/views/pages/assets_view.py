# src/views/pages/assets_view.py
import streamlit as st
from decimal import Decimal
from datetime import date
from src.container import get_container
from src.domain.enums import AssetCategory, LiabilityCategory, CashCategory, Currency
from src.views.components.kpi_cards import render_executive_summary_cards


# --- HELPER: ASSET CARD ---
def render_asset_card(asset, service, icon: str):
    """
    Renders a 'Smart Card' for an asset with a Popover for editing details.
    """
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])

        # 1. Clean Summary View
        with c1:
            st.markdown(f"### {icon} {asset.name}")
            # Dynamic Subtitle based on category
            details = []
            if asset.category == AssetCategory.REAL_ESTATE:
                if asset.address: details.append(asset.address)
                if asset.area_m2: details.append(f"{asset.area_m2} m²")

            elif asset.category == AssetCategory.VEHICLE:
                if asset.brand: details.append(asset.brand)
                if asset.model: details.append(asset.model)


            elif asset.category == AssetCategory.CASH:
                if asset.bucket_name: details.append(f"📂 {asset.bucket_name}")
                if asset.cash_type: details.append(asset.cash_type)

                # Banking Details
                acc_info = []
                if asset.account_number:
                    acc_str = asset.account_number
                    if asset.bank_code: acc_str += f"/{asset.bank_code}"
                    acc_info.append(acc_str)
                if asset.iban: acc_info.append(asset.iban)
                if acc_info: details.append(" • ".join(acc_info))

            if details:
                st.caption(" • ".join(details))

        with c2:
            st.metric("Value", f"{asset.value:,.0f} {asset.currency.value}")

        # 2. Edit Menu (Popover)
        with c3:
            with st.popover("⚙️ Manage", use_container_width=True):
                st.markdown("#### Edit Details")
                with st.form(key=f"edit_asset_{asset.id}"):
                    new_name = st.text_input("Name", value=asset.name)
                    new_val = st.number_input("Value", value=float(asset.value), step=1000.0, format="%0.f")

                    # Category Specific Fields
                    # Category Specific Fields
                    kwargs = {}
                    if asset.category == AssetCategory.REAL_ESTATE:
                        kwargs['address'] = st.text_input("Address", value=asset.address or "")
                        kwargs['area_m2'] = Decimal(st.number_input("Area (m²)", value=float(asset.area_m2 or 0)))

                    elif asset.category == AssetCategory.VEHICLE:
                        kwargs['brand'] = st.text_input("Brand", value=asset.brand or "")
                        kwargs['model'] = st.text_input("Model", value=asset.model or "")
                        kwargs['insurance_cost'] = Decimal(
                            st.number_input("Annual Insurance", value=float(asset.insurance_cost or 0)))

                    elif asset.category == AssetCategory.CASH:
                        kwargs['bucket_name'] = st.text_input("Envelope / Bucket Name", value=asset.bucket_name or "",
                                                              placeholder="e.g. Vacation Fund")

                        c_acc, c_bank = st.columns(2)
                        kwargs['account_number'] = c_acc.text_input("Account Number", value=asset.account_number or "")
                        kwargs['bank_code'] = c_bank.text_input("Bank Code", value=asset.bank_code or "")

                        kwargs['iban'] = st.text_input("IBAN (USD/EUR)", value=asset.iban or "")
                    c_save, c_del = st.columns(2)
                    if c_save.form_submit_button("💾 Save Changes", type="primary"):
                        # Update core fields
                        asset.name = new_name
                        # Update extra fields
                        for k, v in kwargs.items():
                            setattr(asset, k, v)

                        service.update_asset_value(asset, Decimal(new_val))
                        st.toast(f"Updated {asset.name}")
                        st.rerun()

                    if c_del.form_submit_button("🗑️ Delete Asset"):
                        service.delete_asset(asset.id)
                        st.rerun()


# --- HELPER: LIABILITY CARD ---
def render_liability_card(liab, service):
    """
    Renders a 'Smart Card' for a liability with detailed editing.
    """
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])

        # 1. Clean Summary
        with c1:
            st.markdown(f"### 💳 {liab.name}")
            details = [liab.liability_type.value]
            if liab.interest_rate:
                details.append(f"**{liab.interest_rate}% APR**")
            if liab.monthly_payment_day:
                details.append(f"Due day: {liab.monthly_payment_day}.")

            st.caption(" • ".join(details))

        with c2:
            # Red color for debt
            st.markdown(f"<h2 style='color: #FF4B4B; margin:0;'>-{liab.amount:,.0f} {liab.currency.value}</h2>",
                        unsafe_allow_html=True)
            if liab.repayment_end_date:
                st.caption(f"End Date: {liab.repayment_end_date}")

        # 2. Edit Menu (Popover)
        with c3:
            with st.popover("⚙️ Manage", use_container_width=True):
                st.markdown("#### Update Liability")
                with st.form(key=f"edit_liab_{liab.id}"):
                    new_name = st.text_input("Name", value=liab.name)
                    new_amount = st.number_input("Outstanding Balance", value=float(liab.amount), step=1000.0)

                    c_rate, c_day = st.columns(2)
                    new_rate = c_rate.number_input("Interest Rate (%)", value=float(liab.interest_rate or 0.0),
                                                   step=0.1)
                    new_day = c_day.number_input("Payment Day", min_value=1, max_value=31,
                                                 value=liab.monthly_payment_day or 15)

                    new_end = st.date_input("End Date", value=liab.repayment_end_date or None)

                    c_save, c_del = st.columns(2)
                    if c_save.form_submit_button("💾 Update", type="primary"):
                        service.update_liability_details(
                            liab,
                            name=new_name,
                            amount=Decimal(new_amount),
                            interest_rate=Decimal(new_rate),
                            monthly_payment_day=new_day,
                            repayment_end_date=new_end
                        )
                        st.toast("Liability Updated")
                        st.rerun()

                    if c_del.form_submit_button("🗑️ Delete"):
                        service.delete_liability(liab.id)
                        st.rerun()


# --- MAIN VIEW ---
def render_view():
    st.title("🏛️ Assets & Liabilities")

    container = get_container()
    asset_svc = container['asset']
    liab_svc = container['liability']
    summary_data = container['summary'].get_executive_summary()

    assets = asset_svc.get_user_assets()
    liabilities = liab_svc.get_user_liabilities()

    render_executive_summary_cards(summary_data)

    # Removed Equity as requested
    t_re, t_veh, t_cash, t_liab = st.tabs(["🏡 Real Estate", "🚗 Vehicles", "💰 Cash", "💳 Liabilities"])

    # --- 1. REAL ESTATE ---
    with t_re:
        re_assets = [a for a in assets if a.category == AssetCategory.REAL_ESTATE]
        for a in re_assets: render_asset_card(a, asset_svc, "🏡")

        st.divider()
        with st.expander("➕ Add Property"):
            with st.form("add_re"):
                c1, c2 = st.columns(2)
                name = c1.text_input("Property Name")
                addr = c2.text_input("Address")
                c3, c4 = st.columns(2)
                val = c3.number_input("Current Value", step=10000.0)
                m2 = c4.number_input("Area (m²)", step=1.0)

                if st.form_submit_button("Add Property", type="primary"):
                    asset_svc.create_asset(name, AssetCategory.REAL_ESTATE, Decimal(val), address=addr,
                                           area_m2=Decimal(m2))
                    st.rerun()

    # --- 2. VEHICLES ---
    with t_veh:
        veh_assets = [a for a in assets if a.category == AssetCategory.VEHICLE]
        for a in veh_assets: render_asset_card(a, asset_svc, "🚗")

        st.divider()
        with st.expander("➕ Add Vehicle"):
            with st.form("add_veh"):
                c1, c2 = st.columns(2)
                brand = c1.text_input("Brand")
                model = c2.text_input("Model")
                c3, c4 = st.columns(2)
                val = c3.number_input("Current Value", step=5000.0)
                ins = c4.number_input("Annual Insurance", step=100.0)

                if st.form_submit_button("Add Vehicle", type="primary"):
                    asset_svc.create_asset(f"{brand} {model}", AssetCategory.VEHICLE, Decimal(val), brand=brand,
                                           model=model, insurance_cost=Decimal(ins))
                    st.rerun()

        # --- 3. CASH ---
        with t_cash:
            cash_assets = [a for a in assets if a.category == AssetCategory.CASH]
            for a in cash_assets: render_asset_card(a, asset_svc, "💰")
            st.divider()
            with st.expander("➕ Add Cash Asset"):
                with st.form("add_cash"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Account / Bucket Name")
                    c_type = c2.selectbox("Type", [t.value for t in CashCategory])

                    c3, c4 = st.columns(2)
                    val = c3.number_input("Amount", step=1000.0)
                    curr = c4.selectbox("Currency", [c.value for c in Currency])

                    # Banking Details
                    st.markdown("___")
                    st.caption("Banking Details (Optional)")
                    b1, b2 = st.columns(2)
                    acc = b1.text_input("Account Number")
                    code = b2.text_input("Bank Code")
                    iban = st.text_input("IBAN (For Foreign Accounts)")
                    env = st.text_input("Linked Envelope / Bucket Name", help="Logical grouping for this money")

                    if st.form_submit_button("Add Cash", type="primary"):
                        asset_svc.create_asset(
                            name, AssetCategory.CASH, Decimal(val), currency=curr, cash_type=c_type,
                            account_number=acc, bank_code=code, iban=iban, bucket_name=env
                        )
                        st.rerun()

        # --- 4. LIABILITIES ---
        with t_liab:
            for l in liabilities: render_liability_card(l, liab_svc)
            st.divider()
            with st.expander("➕ Add Liability"):
                with st.form("add_liab"):
                    c1, c2 = st.columns(2)
                    name = c1.text_input("Name (e.g. Mortgage)")
                    l_type = c2.selectbox("Type", [t.value for t in LiabilityCategory])

                    # NEW FIELD
                    inst = st.text_input("Institution / Lender", placeholder="e.g. Chase Bank")

                    c3, c4 = st.columns(2)
                    amt = c3.number_input("Outstanding Balance", step=10000.0)
                    rate = c4.number_input("Interest Rate (%)", step=0.1)

                    if st.form_submit_button("Add Liability", type="primary"):
                        liab_svc.create_liability(name, Decimal(amt), l_type, institution=inst,
                                                  interest_rate=Decimal(rate))
                        st.rerun()