# src/core/security_config.py
"""
Security configuration for the Family Office Tracker application.
Centralizes security-related settings for authentication and session management.
"""
import os
from pathlib import Path

# Password Hashing
BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))  # 12 rounds is a good balance

# Username HMAC
# In production, this should be set via environment variable
# For development, we use a default that gets generated on first use
USERNAME_HMAC_SECRET = os.getenv("USERNAME_HMAC_SECRET", None)

# Session Management
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))  # 30 minutes default
SESSION_CHECK_ENABLED = os.getenv("SESSION_CHECK_ENABLED", "true").lower() == "true"

# Rate Limiting
LOGIN_RATE_LIMIT_ATTEMPTS = int(os.getenv("LOGIN_RATE_LIMIT_ATTEMPTS", "5"))  # 5 attempts
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300"))  # 5 minutes
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

# Secret Key Storage
SECRETS_DIR = Path("data") / ".secrets"

def get_or_create_hmac_secret() -> str:
    """
    Get the HMAC secret from environment or generate one if it doesn't exist.
    In production, this should always come from environment variables.
    """
    if USERNAME_HMAC_SECRET:
        return USERNAME_HMAC_SECRET
    
    # For development, generate and store a secret
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    secret_file = SECRETS_DIR / "hmac_secret.txt"
    
    if secret_file.exists():
        return secret_file.read_text().strip()
    
    # Generate a new secret
    import secrets
    secret = secrets.token_hex(32)  # 256-bit secret
    secret_file.write_text(secret)
    secret_file.chmod(0o600)  # Read/write for owner only
    return secret
