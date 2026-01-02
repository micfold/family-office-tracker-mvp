# src/views/components/asset_cards.py
import streamlit as st
from src.domain.models.MAsset import Asset
from src.domain.enums import AssetCategory

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
                st.markdown(f"**Type:** {asset.cash_type}")
                st.markdown(f"**Account:** {asset.account_identifier}")
                if asset.bucket_name:
                    st.markdown(f"**Bucket:** {asset.bucket_name}")

            st.markdown("---")
            if st.button("Delete Asset", key=f"delete_btn_{asset.id}"):
                on_delete(asset.id)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

