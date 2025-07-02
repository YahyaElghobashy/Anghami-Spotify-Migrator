"""
Security module for Anghami → Spotify Migration Backend
Contains encryption, key vault management, and authentication functions
"""

from .encryption import (
    init_secure_key_vault,
    get_master_key,
    store_encryption_key,
    get_encryption_key,
    remove_encryption_key,
    encrypt_credential,
    decrypt_credential,
    secure_decrypt_credential
)

from .authentication import (
    generate_user_id,
    generate_session_token,
    validate_session_token,
    hash_password,
    verify_password,
    generate_api_key,
    is_session_expired
)

__all__ = [
    # Encryption functions
    "init_secure_key_vault",
    "get_master_key",
    "store_encryption_key",
    "get_encryption_key",
    "remove_encryption_key",
    "encrypt_credential",
    "decrypt_credential",
    "secure_decrypt_credential",
    # Authentication functions
    "generate_user_id",
    "generate_session_token",
    "validate_session_token",
    "hash_password",
    "verify_password",
    "generate_api_key",
    "is_session_expired"
]
