# app.py
import streamlit as st
import sys
from pathlib import Path
# Add project root to path to allow for absolute imports from `config.py`
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.application.auth_service import AuthService

# Import NEW Views
from src.views.pages import (
    assets_view,
    dashboard_view,
    portfolio_view,
    cashflow_view,
)

# Page Config
st.set_page_config(page_title="Family Office", layout="wide", page_icon="🏛️")

# Initialize Auth
auth = AuthService()

# --- Main App Router ---
if not st.session_state.get("logged_in"):
    # --- 1. LOGIN SCREEN ---
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🏛️ Family Office Tracker")
        with st.form("login_form"):
            st.subheader("Secure Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Enter Office", type="primary"):
                if auth.login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid username or password")
else:
    # --- 2. RENDER THE APP ---
    user = auth.current_user
    page = None

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 👤 {user['username']}")
        st.success("Logged in")

        # --- TAX REGION SELECTOR ---
        st.selectbox(
            "Tax Region",
            ["Czech Republic", "Other"],
            index=0,
            key="tax_region"
        )

        # --- NAVIGATION ---
        page = st.radio(
            "Navigation",
            ("Dashboard", "Assets", "Portfolio", "Cashflow")
        )

        st.divider()
        if st.button("Log Out"):
            auth.logout()
            st.rerun()

    # --- MAIN CONTENT AREA ---
    if page == "Dashboard":
        dashboard_view.render_view()
    elif page == "Assets":
        assets_view.render_view()
    elif page == "Portfolio":
        portfolio_view.render_view()
    elif page == "Cashflow":
        cashflow_view.render_view()
    else:
        # Default to dashboard
        dashboard_view.render_view()
