# services/auth_service.py
import streamlit as st
import json
import hashlib
import hmac
import bcrypt
from pathlib import Path
from uuid import uuid4
import logging
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from src.core.security_config import (
    BCRYPT_ROUNDS,
    get_or_create_hmac_secret,
    SESSION_TIMEOUT_MINUTES,
    SESSION_CHECK_ENABLED,
    LOGIN_RATE_LIMIT_ATTEMPTS,
    LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_ENABLED
)

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
        
        # Rate limiting storage (in-memory, resets on restart)
        self._login_attempts = defaultdict(list)
        
        # Get or create HMAC secret
        self._hmac_secret = get_or_create_hmac_secret()

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

    def _hash_password_bcrypt(self, password: str) -> str:
        """Hash password using bcrypt (current method)."""
        # Do NOT log passwords
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        return bcrypt.hashpw(password.encode(), salt).decode('utf-8')
    
    def _verify_password_bcrypt(self, password: str, hashed: str) -> bool:
        """Verify password against bcrypt hash."""
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode('utf-8'))
        except Exception as e:
            logger.debug("bcrypt verification failed: %s", e)
            return False

    def _hash_password_sha256(self, password: str) -> str:
        """Legacy SHA-256 password hashing (for migration only)."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify password against stored hash.
        Supports both bcrypt (current) and SHA-256 (legacy).
        """
        # Bcrypt hashes start with $2a$, $2b$, or $2y$
        if stored_hash.startswith('$2'):
            return self._verify_password_bcrypt(password, stored_hash)
        else:
            # Legacy SHA-256
            return self._hash_password_sha256(password) == stored_hash

    def _hash_username(self, username: str) -> str:
        """
        Hash username with HMAC-SHA256 using server secret.
        This prevents rainbow table attacks on usernames.
        """
        return hmac.new(
            self._hmac_secret.encode(),
            username.encode(),
            hashlib.sha256
        ).hexdigest()

    def _check_rate_limit(self, username_key: str) -> bool:
        """
        Check if login attempts for this user are within rate limits.
        Returns True if allowed, False if rate limited.
        """
        if not RATE_LIMIT_ENABLED:
            return True
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=LOGIN_RATE_LIMIT_WINDOW_SECONDS)
        
        # Clean old attempts
        self._login_attempts[username_key] = [
            attempt for attempt in self._login_attempts[username_key]
            if attempt > cutoff
        ]
        
        # Check limit
        if len(self._login_attempts[username_key]) >= LOGIN_RATE_LIMIT_ATTEMPTS:
            logger.warning("Rate limit exceeded for user_key=%s", username_key[:8])
            return False
        
        return True
    
    def _record_login_attempt(self, username_key: str):
        """Record a failed login attempt for rate limiting."""
        if RATE_LIMIT_ENABLED:
            self._login_attempts[username_key].append(datetime.now())

    def _check_session_expiration(self) -> bool:
        """
        Check if the current session has expired.
        Returns True if session is valid, False if expired.
        """
        if not SESSION_CHECK_ENABLED:
            return True
        
        user = st.session_state.get("user")
        if not user:
            return False
        
        last_activity = user.get("last_activity")
        if not last_activity:
            # Set last activity if not present (backward compatibility)
            user["last_activity"] = datetime.now().isoformat()
            st.session_state["user"] = user
            return True
        
        last_activity_dt = datetime.fromisoformat(last_activity)
        timeout = timedelta(minutes=SESSION_TIMEOUT_MINUTES)
        
        if datetime.now() - last_activity_dt > timeout:
            logger.info("Session expired for user id=%s", user.get("id"))
            return False
        
        return True
    
    def _update_session_activity(self):
        """Update the last activity timestamp for session management."""
        if SESSION_CHECK_ENABLED:
            user = st.session_state.get("user")
            if user:
                user["last_activity"] = datetime.now().isoformat()
                st.session_state["user"] = user

    # ---------- public API ----------

    def login(self, username: str, password: str) -> bool:
        if not username or not password:
            logger.warning("Login attempt with empty username or password")
            return False

        clean_name = username.lower().strip().replace(" ", "_")
        username_key = self._hash_username(clean_name)
        short_key = username_key[:8]

        # Check rate limiting
        if not self._check_rate_limit(username_key):
            logger.warning("Rate limit exceeded for user_key=%s", short_key)
            return False

        users = self._load_users()
        logger.info("Login attempt user_key=%s", short_key)

        user_id: Optional[str] = None
        needs_password_upgrade = False
        
        # User exists → verify password with migration support
        if username_key in users:
            logger.debug("Found hashed user entry user_key=%s", short_key)
            stored_password = users[username_key].get("password")
            
            # Verify password (supports both bcrypt and legacy SHA-256)
            if self._verify_password(password, stored_password):
                user_id = users[username_key].get("id", str(uuid4()))
                users[username_key]["id"] = user_id
                
                # Check if password needs upgrade from SHA-256 to bcrypt
                if not stored_password.startswith('$2'):
                    needs_password_upgrade = True
                    new_hash = self._hash_password_bcrypt(password)
                    users[username_key]["password"] = new_hash
                    logger.info("Upgraded password hash to bcrypt for user_key=%s", short_key)
                
                self._save_users(users)
                logger.info("User logged in id=%s user_key=%s", user_id, short_key)
            else:
                # Try legacy plaintext username key as fallback
                if clean_name in users:
                    legacy_password = users[clean_name].get("password")
                    if self._verify_password(password, legacy_password):
                        logger.info("Legacy plaintext key matches; migrating for user_key=%s", short_key)
                        user_id = users[clean_name].get("id", str(uuid4()))
                        
                        # Upgrade password hash during migration
                        new_hash = self._hash_password_bcrypt(password)
                        users[username_key] = {
                            "username_hashed": username_key,
                            "password": new_hash,
                            "id": user_id
                        }
                        try:
                            del users[clean_name]
                        except KeyError:
                            logger.debug("Legacy plaintext key missing during delete: %s", clean_name)
                        self._save_users(users)
                        logger.info("Migrated and upgraded password for id=%s user_key=%s", user_id, short_key)
                    else:
                        logger.warning("Password mismatch for user_key=%s", short_key)
                        self._record_login_attempt(username_key)
                        return False
                else:
                    logger.warning("Password mismatch for user_key=%s", short_key)
                    self._record_login_attempt(username_key)
                    return False
        elif clean_name in users:
            # Legacy plaintext username key found — verify and migrate
            logger.info("Legacy plaintext user key detected; migrating to user_key=%s", short_key)
            legacy_password = users[clean_name].get("password")
            
            if not self._verify_password(password, legacy_password):
                logger.warning("Password mismatch for legacy key user_key=%s", short_key)
                self._record_login_attempt(username_key)
                return False
            
            user_id = users[clean_name].get("id", str(uuid4()))
            
            # Upgrade password during migration
            new_hash = self._hash_password_bcrypt(password)
            users[username_key] = {
                "username_hashed": username_key,
                "password": new_hash,
                "id": user_id
            }
            try:
                del users[clean_name]
            except KeyError:
                logger.debug("Legacy plaintext key not present: %s", clean_name)
            self._save_users(users)
            logger.info("Migrated and upgraded password for id=%s user_key=%s", user_id, short_key)
        else:
            # Create new user with bcrypt
            user_id = str(uuid4())
            password_hash = self._hash_password_bcrypt(password)
            users[username_key] = {
                "username_hashed": username_key,
                "password": password_hash,
                "id": user_id
            }
            self._save_users(users)
            logger.info("Created new user with bcrypt id=%s user_key=%s", user_id, short_key)

        # Safety check
        if user_id is None:
            logger.error("Login flow failed to establish user id for user_key=%s", short_key)
            self._record_login_attempt(username_key)
            return False

        # Ensure user directory exists
        user_path = DATA_ROOT / user_id
        try:
            user_path.mkdir(exist_ok=True)
            logger.debug("Ensured user directory at %s", user_path)
        except Exception as e:
            logger.exception("Failed to create user directory %s: %s", user_path, e)

        # Set session with activity timestamp
        st.session_state["user"] = {
            "username": username,
            "id": user_id,
            "path": user_path,
            "last_activity": datetime.now().isoformat()
        }
        
        # Clear rate limit on successful login
        if RATE_LIMIT_ENABLED and username_key in self._login_attempts:
            del self._login_attempts[username_key]
        
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
        """
        Get current user, checking for session expiration.
        Returns None if session has expired.
        """
        if not self._check_session_expiration():
            logger.info("Session expired, logging out user")
            self.logout()
            return None
        
        # Update activity timestamp
        self._update_session_activity()
        return st.session_state.get("user")

    def get_file_path(self, filename: str) -> Path:
        if not self.current_user:
            logger.warning("Attempt to resolve file path without logged-in user: %s", filename)
            raise PermissionError("User not logged in.")
        user_id = self.current_user.get("id")
        logger.debug("Resolving file path for user id=%s file=%s", user_id, filename)
        return self.current_user["path"] / filename
