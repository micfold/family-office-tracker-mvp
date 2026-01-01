# services/auth_service.py
import streamlit as st
import json
import hashlib
from pathlib import Path
from uuid import uuid4

DATA_ROOT = Path("data")
USERS_FILE = DATA_ROOT / "users.json"


class AuthService:
    def __init__(self):
        DATA_ROOT.mkdir(exist_ok=True)
        if not USERS_FILE.exists():
            USERS_FILE.write_text(json.dumps({}))

    # ---------- internal helpers ----------

    def _load_users(self) -> dict:
        return json.loads(USERS_FILE.read_text())

    def _save_users(self, users: dict):
        USERS_FILE.write_text(json.dumps(users, indent=2))

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def _hash_username(self, username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()

    # ---------- public API ----------

    def login(self, username: str, password: str) -> bool:
        if not username or not password:
            return False

        clean_name = username.lower().strip().replace(" ", "_")
        users = self._load_users()
        password_hash = self._hash_password(password)

        user_id = None
        # User exists → verify password
        if clean_name in users:
            if users[clean_name]["password"] != password_hash:
                return False
            user_id = users[clean_name].get("id", str(uuid4()))
            users[clean_name]["id"] = user_id
            self._save_users(users)
        else:
            # Create new user (remove this block if you want login-only)
            user_id = str(uuid4())
            users[clean_name] = {
                "username": self._hash_username(clean_name),
                "password": password_hash,
                "id": user_id
            }
            self._save_users(users)

        # Ensure user directory
        user_path = DATA_ROOT / clean_name
        user_path.mkdir(exist_ok=True)

        st.session_state["user"] = {
            "username": username,
            "id": user_id,
            "path": user_path
        }
        return True

    def logout(self):
        st.session_state.pop("user", None)

    @property
    def current_user(self):
        return st.session_state.get("user")

    def get_file_path(self, filename: str) -> Path:
        if not self.current_user:
            raise PermissionError("User not logged in.")
        return self.current_user["path"] / filename
