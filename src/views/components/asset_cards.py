# src/views/components/asset_cards.py
import streamlit as st
from decimal import Decimal
from src.domain.enums import AssetCategory, CashCategory, Currency


def render_asset_card(asset, on_update, on_delete, icon: str):
    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 2, 1])

        # Display Logic
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

        # Edit Logic
        with c3:
            with st.popover("⚙️ Manage", use_container_width=True):
                st.markdown("#### Edit Details")
                with st.form(key=f"edit_asset_{asset.id}"):
                    new_name = st.text_input("Name", value=asset.name)
                    new_val = st.number_input("Value", value=float(asset.value), step=1000.0, format="%0.f")

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

                        on_update(asset, Decimal(new_val))
                        st.toast(f"Updated {asset.name}")
                        st.rerun()

                    if c_del.form_submit_button("🗑️ Delete Asset"):
                        on_delete(asset.id)
                        st.rerun()