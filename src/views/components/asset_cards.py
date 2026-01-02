# src/views/components/asset_cards.py
import streamlit as st
from src.domain.models.MAsset import Asset
from src.domain.enums import AssetCategory
from src.views.components.address_autocomplete import (
    display_location_map,
    render_address_input_with_autocomplete
)

def render_asset_card(asset: Asset, on_update, on_delete, icon):
    """Renders a card for a single asset with options to update or delete."""

    card_style = """
        <style>
            .card {
                border: 1px solid #e6e6e6;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                transition: box-shadow 0.3s;
            }
            .card:hover {
                box-shadow: 0 8px 16px rgba(0,0,0,0.2);
            }
            .color-box {
                width: 20px;
                height: 20px;
                border-radius: 5px;
                display: inline-block;
                vertical-align: middle;
                margin-left: 10px;
            }
        </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)

    with st.container():
        st.markdown(f'<div class="card">', unsafe_allow_html=True)

        c1, c2 = st.columns([3, 1])

        # --- HEADER ---
        name = asset.name or "Unnamed Asset"
        c1.subheader(f"{icon} {name}")
        c2.metric("Current Value", f"{asset.value:,.0f} {asset.currency.value}")

        # --- EXPANDER FOR DETAILS ---
        with st.expander("Details"):
            if asset.category == AssetCategory.REAL_ESTATE:
                st.markdown(f"**Type:** {asset.property_type.value if asset.property_type else 'N/A'}")
                st.markdown(f"**Location:** {asset.address}, {asset.city} {asset.postal_code}")
                st.markdown(f"**Area:** {asset.area_m2} m²")
                st.markdown(f"**Annual Cost:** {asset.annual_cost_projection or 0:,.0f} {asset.currency.value}")

            elif asset.category == AssetCategory.VEHICLE:
                st.markdown(f"**Year:** {asset.year_made}")
                st.markdown(f"**Mileage:** {asset.kilometers_driven:,} km")
                st.markdown(f"**Acquired:** {asset.acquisition_date.strftime('%B %Y') if asset.acquisition_date else 'N/A'}")
                st.markdown(f"**Acquisition Price:** {asset.acquisition_price or 0:,.0f} {asset.currency.value}")
                if asset.color:
                    st.markdown(f'**Color:** <span style="color:{asset.color};">●</span>', unsafe_allow_html=True)

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
