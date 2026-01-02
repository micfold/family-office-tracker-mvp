# src/views/components/asset_cards.py
import streamlit as st
from decimal import Decimal
from src.domain.enums import AssetCategory
from src.views.components.address_autocomplete import display_location_map


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
        
        # Display map for real estate if coordinates available
        if asset.category == AssetCategory.REAL_ESTATE and asset.latitude and asset.longitude:
            with c1:
                with st.expander("📍 View Location Map"):
                    display_location_map(asset.latitude, asset.longitude, width=400, height=200)

        with c2:
            st.metric("Value", f"{asset.value:,.0f} {asset.currency.value}")

        # Edit Logic
        with c3:
            with st.popover("⚙️ Manage", use_container_width=True):
                st.markdown("#### Edit Details")
                _render_edit_form(asset, on_update, on_delete)


def _render_edit_form(asset, on_update, on_delete):
    """Render edit form outside of main card to support address autocomplete"""
    from src.views.components.address_autocomplete import render_address_input_with_autocomplete
    
    # For real estate with address autocomplete (outside form)
    if asset.category == AssetCategory.REAL_ESTATE:
        st.markdown("**Basic Information**")
        new_name = st.text_input("Name", value=asset.name, key=f"edit_name_{asset.id}")
        new_val = st.number_input("Value", value=float(asset.value), step=1000.0, format="%0.f", key=f"edit_val_{asset.id}")
        
        st.markdown("---")
        st.markdown("**📍 Property Location**")
        
        # Address autocomplete with real-time suggestions
        address, lat, lng = render_address_input_with_autocomplete(
            label="Address",
            key_prefix=f"edit_re_{asset.id}",
            default_value=asset.address or "",
            default_lat=asset.latitude,
            default_lng=asset.longitude
        )
        
        area = st.number_input("Area (m²)", value=float(asset.area_m2 or 0), key=f"edit_area_{asset.id}")
        
        # Save and delete buttons
        c_save, c_del = st.columns(2)
        if c_save.button("💾 Save", type="primary", key=f"save_btn_{asset.id}", use_container_width=True):
            # Prepare update payload
            kwargs = {
                'name': new_name,
                'address': address,
                'area_m2': Decimal(area)
            }
            if lat and lng:
                kwargs['latitude'] = lat
                kwargs['longitude'] = lng
            
            on_update(asset.id, new_value=Decimal(new_val), **kwargs)
            st.toast(f"Updated {new_name}")
            st.rerun()
        
        if c_del.button("🗑️ Delete", key=f"del_btn_{asset.id}", use_container_width=True):
            on_delete(asset.id)
            st.rerun()
    
    else:
        # For other asset types, use form as before
        with st.form(key=f"edit_asset_{asset.id}"):
            new_name = st.text_input("Name", value=asset.name)
            new_val = st.number_input("Value", value=float(asset.value), step=1000.0, format="%0.f")

            # Category Specific Fields
            kwargs = {}
            if asset.category == AssetCategory.VEHICLE:
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
                # Collect update payload (do not mutate `asset` directly in the view)
                update_payload = {'name': new_name, 'value': Decimal(new_val)}
                update_payload.update(kwargs)

                # Call the service-level updater which accepts asset_id and kwargs
                on_update(asset.id, new_value=update_payload['value'], **{k: v for k, v in update_payload.items() if k != 'value'})

                st.toast(f"Updated {new_name}")
                st.rerun()

            if c_del.form_submit_button("🗑️ Delete Asset"):
                on_delete(asset.id)
                st.rerun()