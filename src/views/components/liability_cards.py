# src/views/components/liability_cards.py
import streamlit as st
from src.domain.models.MLiability import Liability
from src.views.utils import format_currency
from src.views.utils import calculate_czech_mortgage_deduction
from src.domain.enums import LiabilityCategory


def render_liability_card(liability: Liability, on_update, on_delete, icon):
    """Renders a card for a single liability with options to update or delete."""

    card_style = """
        <style>
            .card {
                border: 1px solid #e6e6e6;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }
        </style>
    """
    st.markdown(card_style, unsafe_allow_html=True)

    with st.container():
        st.markdown(f'<div class="card">', unsafe_allow_html=True)

        c1, c2 = st.columns([3, 1])

        # --- HEADER ---
        name = f"{liability.liability_type.value} from {liability.institution}"
        c1.subheader(f"{icon} {name}")
        c2.metric("Outstanding", f"{liability.amount:,.0f} {liability.currency.value}")

        # --- EXPANDER FOR DETAILS ---
        with st.expander("Details"):
            st.markdown(f"**Interest Rate:** {liability.interest_rate}%")
            if liability.has_insurance:
                st.markdown(f"**Insurance Cost:** {liability.insurance_cost or 0:,.0f} {liability.currency.value} / year")

            # --- Mortgage Tax Deduction ---
            if liability.liability_type == LiabilityCategory.MORTGAGE and liability.start_date and liability.annual_interest_paid:
                st.markdown("---")
                st.markdown(f"**Start Date:** {liability.start_date.strftime('%B %Y')}")
                st.markdown(f"**Annual Interest Paid:** {liability.annual_interest_paid:,.0f} {liability.currency.value}")

                tax_region = st.session_state.get("tax_region", "Other")
                deduction = calculate_czech_mortgage_deduction(
                    start_date=liability.start_date,
                    annual_interest_paid=liability.annual_interest_paid,
                    tax_region=tax_region
                )
                if deduction > 0:
                    st.success(f"**Tax Deduction:** {format_currency(deduction, liability.currency.value)} {liability.currency.value}", icon="✅")

            st.markdown("---")
            if st.button("Delete Liability", key=f"delete_liab_btn_{liability.id}"):
                on_delete(liability.id)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
