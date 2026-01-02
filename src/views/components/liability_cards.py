# src/views/components/liability_cards.py
import streamlit as st
from decimal import Decimal


def render_liability_card(liab, on_update, on_delete, icon: str):
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
                        on_update(
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
                        on_delete(liab.id)
                        st.rerun()