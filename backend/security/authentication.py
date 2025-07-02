"""
Module: Authentication
Purpose: User authentication utilities including ID and session token generation
Contains: generate_user_id, generate_session_token, validate_session_token
"""

import secrets
import hashlib
import time
from typing import Optional
from datetime import datetime, timedelta

def generate_user_id() -> str:
    """Generate a unique user ID"""
    # Use timestamp + random component for uniqueness
    timestamp = str(int(time.time()))
    random_part = secrets.token_hex(8)
    
    # Create a hash to make it less predictable
    combined = f"{timestamp}_{random_part}"
    user_id = hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    return user_id

def generate_session_token() -> str:
    """Generate a secure session token"""
    # Generate a 32-byte random token
    return secrets.token_urlsafe(32)

def validate_session_token(token: str) -> bool:
    """Validate session token format"""
    if not token:
        return False
    
    # Basic validation - should be a proper URL-safe base64 string
    try:
        # Check if it's a reasonable length (32 bytes -> ~43 chars in base64)
        if len(token) < 20 or len(token) > 100:
            return False
        
        # Check if it contains only valid URL-safe base64 characters
        import base64
        base64.urlsafe_b64decode(token + '==')  # Add padding if needed
        return True
    except:
        return False

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash a password with salt"""
    if not salt:
        salt = secrets.token_hex(16)
    
    # Use PBKDF2 for secure password hashing
    import hashlib
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return hashed.hex(), salt

def verify_password(password: str, hashed_password: str, salt: str) -> bool:
    """Verify a password against its hash"""
    try:
        new_hash, _ = hash_password(password, salt)
        return new_hash == hashed_password
    except:
        return False

def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"anghami_spotify_{secrets.token_urlsafe(32)}"

def is_session_expired(created_at: str, expiry_days: int = 30) -> bool:
    """Check if a session has expired"""
    try:
        created_datetime = datetime.fromisoformat(created_at)
        expiry_datetime = created_datetime + timedelta(days=expiry_days)
        return datetime.now() > expiry_datetime
    except:
        return True  # If we can't parse the date, consider it expired 