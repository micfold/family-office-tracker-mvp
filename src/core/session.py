# src/core/session.py
import streamlit as st
from typing import Optional, Dict, Any
from uuid import UUID

class SessionManager:
    """
    Type-safe wrapper around st.session_state.
    Single source of truth for session keys.
    """
    KEY_USER = "user"
    KEY_TOAST = "toast_message"

    @staticmethod
    def get_user_id() -> UUID:
        user = st.session_state.get(SessionManager.KEY_USER)
        if not user:
            raise PermissionError("User not logged in")
        return UUID(user["id"])

    @staticmethod
    def get_user_data() -> Optional[Dict[str, Any]]:
        return st.session_state.get(SessionManager.KEY_USER)

    @staticmethod
    def set_user(user_data: Dict[str, Any]):
        st.session_state[SessionManager.KEY_USER] = user_data

    @staticmethod
    def logout():
        if SessionManager.KEY_USER in st.session_state:
            del st.session_state[SessionManager.KEY_USER]

    @staticmethod
    def show_toast_if_pending():
        msg = st.session_state.get(SessionManager.KEY_TOAST)
        if msg:
            st.toast(msg)
            del st.session_state[SessionManager.KEY_TOAST]

    @staticmethod
    def set_toast(message: str):
        st.session_state[SessionManager.KEY_TOAST] = message