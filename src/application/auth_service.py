# services/auth_service.py
import streamlit as st
import json
import hashlib
from pathlib import Path
from uuid import uuid4
import logging
from typing import Optional

DATA_ROOT = Path("data")
USERS_FILE = DATA_ROOT / "users.json"

# Module logger
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class AuthService:
    def __init__(self):
        DATA_ROOT.mkdir(exist_ok=True)
        if not USERS_FILE.exists():
            USERS_FILE.write_text(json.dumps({}))
        logger.debug("AuthService initialized; users file=%s", USERS_FILE)

    # ---------- internal helpers ----------

    def _load_users(self) -> dict:
        logger.debug("Loading users from %s", USERS_FILE)
        try:
            return json.loads(USERS_FILE.read_text())
        except Exception as e:
            logger.exception("Failed to load users file: %s", e)
            return {}

    def _save_users(self, users: dict):
        try:
            USERS_FILE.write_text(json.dumps(users, indent=2))
            logger.debug("Saved users file with %d entries", len(users))
        except Exception as e:
            logger.exception("Failed to save users file: %s", e)

    def _hash_password(self, password: str) -> str:
        # Do NOT log passwords
        return hashlib.sha256(password.encode()).hexdigest()

    def _hash_username(self, username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()

    # ---------- public API ----------

    def login(self, username: str, password: str) -> bool:
        if not username or not password:
            logger.warning("Login attempt with empty username or password")
            return False

        clean_name = username.lower().strip().replace(" ", "_")
        users = self._load_users()
        password_hash = self._hash_password(password)

        username_key = self._hash_username(clean_name)
        short_key = username_key[:8]

        logger.info("Login attempt user_key=%s", short_key)

        user_id: Optional[str] = None
        # User exists → verify password. Support legacy plaintext keys by migrating them.
        if username_key in users:
            logger.debug("Found hashed user entry user_key=%s", short_key)
            # modern hashed-key user
            if users[username_key].get("password") == password_hash:
                user_id = users[username_key].get("id", str(uuid4()))
                users[username_key]["id"] = user_id
                self._save_users(users)
                logger.info("User logged in id=%s user_key=%s", user_id, short_key)
            else:
                # Hashed-key exists but password mismatch. Try legacy plaintext key as fallback (handle partial migrations)
                if clean_name in users and users[clean_name].get("password") == password_hash:
                    logger.info("Hashed-key password mismatch but legacy plaintext key matches; migrating legacy entry for user_key=%s", short_key)
                    user_id = users[clean_name].get("id", str(uuid4()))
                    users[username_key] = {
                        "username_hashed": username_key,
                        "password": users[clean_name].get("password"),
                        "id": user_id
                    }
                    try:
                        del users[clean_name]
                    except KeyError:
                        logger.debug("Legacy plaintext key missing during migration delete: %s", clean_name)
                    self._save_users(users)
                    logger.info("Migrated legacy plaintext user to hashed key id=%s user_key=%s", user_id, short_key)
                else:
                    logger.warning("Password mismatch for user_key=%s", short_key)
                    return False
        elif clean_name in users:
            logger.info("Legacy plaintext user key detected for masked user; migrating to hashed key user_key=%s", short_key)
            # legacy plaintext username key found — verify and migrate
            if users[clean_name].get("password") != password_hash:
                logger.warning("Password mismatch for legacy plaintext key (masked) user_key=%s", short_key)
                return False
            # retrieve or create id
            user_id = users[clean_name].get("id", str(uuid4()))
            # create new hashed-key entry and remove plaintext key
            users[username_key] = {
                "username_hashed": username_key,
                "password": users[clean_name].get("password"),
                "id": user_id
            }
            # remove legacy key
            try:
                del users[clean_name]
            except KeyError:
                logger.debug("Legacy plaintext key not present when attempting delete: %s", clean_name)
            self._save_users(users)
            logger.info("Migrated legacy user to id=%s user_key=%s", user_id, short_key)
        else:
            # Create new user (remove this block if you want login-only)
            user_id = str(uuid4())
            users[username_key] = {
                "username_hashed": username_key,
                "password": password_hash,
                "id": user_id
            }
            self._save_users(users)
            logger.info("Created new user id=%s user_key=%s", user_id, short_key)

        # Safety check: ensure user_id is set before proceeding
        if user_id is None:
            logger.error("Login flow failed to establish a user id for user_key=%s", short_key)
            return False

        # Ensure user directory uses user id (avoid storing plaintext usernames on disk)
        user_path = DATA_ROOT / user_id
        try:
            user_path.mkdir(exist_ok=True)
            logger.debug("Ensured user directory at %s", user_path)
        except Exception as e:
            logger.exception("Failed to create user directory %s: %s", user_path, e)

        # Session keeps the readable username, but storage now only has hashed username
        st.session_state["user"] = {
            "username": username,
            "id": user_id,
            "path": user_path
        }
        return True

    def logout(self):
        user = st.session_state.get("user")
        if user:
            logger.info("User logged out id=%s", user.get("id"))
        else:
            logger.debug("Logout called but no user in session")
        st.session_state.pop("user", None)

    @property
    def current_user(self):
        return st.session_state.get("user")

    def get_file_path(self, filename: str) -> Path:
        if not self.current_user:
            logger.warning("Attempt to resolve file path without logged-in user: %s", filename)
            raise PermissionError("User not logged in.")
        user_id = self.current_user.get("id")
        logger.debug("Resolving file path for user id=%s file=%s", user_id, filename)
        return self.current_user["path"] / filename
