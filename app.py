# app.py
import streamlit as st
from services.auth import AuthService # Auth hasn't been fully refactored yet, keeping legacy for now

# Import NEW Views
from src.views.pages import dashboard_view
from src.views.pages import assets_view
from src.views.pages import cashflow_view
from src.views.pages import portfolio_view

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
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Enter Office", type="primary"):
                if auth.login(username, password):
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    st.stop()

# --- 2. SIDEBAR ---
user = auth.current_user
with st.sidebar:
    st.markdown(f"### 👤 {user['username']}")
    nav = st.radio("Control Tower", ["Dashboard", "Assets", "Cashflow", "Portfolio"])
    st.divider()
    if st.button("Log Out"):
        auth.logout()
        st.rerun()

# --- 3. ROUTING ---
if nav == "Dashboard":
    dashboard_view.render_view()
elif nav == "Assets":
    assets_view.render_view()
elif nav == "Cashflow":
    cashflow_view.render_view()
elif nav == "Portfolio":
    portfolio_view.render_view()