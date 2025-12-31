# app.py
import streamlit as st
from services.auth import AuthService
from views import dashboard, assets, cashflow, portfolio

# Page Config
st.set_page_config(page_title="Family Office HQ", layout="wide", page_icon="🏛️")

# Initialize Auth
auth = AuthService()

# --- 1. LOGIN SCREEN ---
if not auth.current_user:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏛️ Family Office Tracker")
        with st.form("login_form"):
            st.subheader("Secure Login")

            username = st.text_input(
                "Username",
                placeholder="e.g. username"
            )
            password = st.text_input(
                "Password",
                type="password",
                placeholder = "e.g. pass"
            )

            submitted = st.form_submit_button(
                "Enter Office",
                type="primary"
            )

            if submitted:
                if auth.login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    st.stop()


# --- 2. SIDEBAR NAVIGATION ---
user = auth.current_user
with st.sidebar:
    st.markdown(f"### 👤 {user['username']}")
    if st.button("Log Out", type="secondary"):
        auth.logout()
        st.rerun()

    st.divider()

    nav = st.radio(
        "Control Tower",
        ["Dashboard", "Assets", "Cashflow", "Portfolio"]
    )

# --- 3. ROUTER ---
if nav == "Dashboard":
    dashboard.render_view()
elif nav == "Assets":
    assets.render_view()
elif nav == "Cashflow":
    cashflow.render_view()
elif nav == "Portfolio":
    portfolio.render_view()