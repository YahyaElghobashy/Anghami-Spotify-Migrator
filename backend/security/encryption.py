"""
Module: Encryption & Key Vault
Purpose: Secure encryption, decryption, and key vault management
Contains: Key vault operations, credential encryption/decryption, master key management
"""

import os
import json
import base64
import secrets
from datetime import datetime
from typing import Optional, Tuple
from cryptography.fernet import Fernet
from ..core.config import SECURE_KEY_VAULT_PATH, DATA_DIR
from ..core.logging import get_logger

logger = get_logger(__name__)

def init_secure_key_vault():
    """Initialize secure key vault separated from main database"""
    # Create key vault file if it doesn't exist
    if not os.path.exists(SECURE_KEY_VAULT_PATH):
        logger.info("Creating secure key vault...")
        # Generate a master encryption key for the vault itself
        master_key = Fernet.generate_key()
        
        # Store initial empty vault structure
        vault_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "keys": {}
        }
        
        fernet = Fernet(master_key)
        encrypted_vault = fernet.encrypt(json.dumps(vault_data).encode())
        
        # Store the encrypted vault and master key separately
        with open(SECURE_KEY_VAULT_PATH, "wb") as f:
            f.write(encrypted_vault)
        
        # Store master key in a separate location (in production, this would be environment/HSM)
        master_key_path = DATA_DIR / ".master_key"
        with open(master_key_path, "wb") as f:
            f.write(master_key)
        
        # Secure the files (Unix permissions)
        os.chmod(SECURE_KEY_VAULT_PATH, 0o600)  # Read/write for owner only
        os.chmod(master_key_path, 0o600)
        
        logger.info("✅ Secure key vault created with restricted permissions")

def get_master_key() -> bytes:
    """Get the master key for the vault"""
    master_key_path = DATA_DIR / ".master_key"
    if not master_key_path.exists():
        raise Exception("Master key not found. Vault may be corrupted.")
    
    with open(master_key_path, "rb") as f:
        return f.read()

def store_encryption_key(user_id: str, encryption_key: str) -> None:
    """Store user's encryption key in secure vault"""
    try:
        master_key = get_master_key()
        fernet = Fernet(master_key)
        
        # Read current vault
        with open(SECURE_KEY_VAULT_PATH, "rb") as f:
            encrypted_vault = f.read()
        
        decrypted_vault = fernet.decrypt(encrypted_vault)
        vault_data = json.loads(decrypted_vault.decode())
        
        # Store the key
        vault_data["keys"][user_id] = {
            "encryption_key": encryption_key,
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        
        # Re-encrypt and store
        encrypted_vault = fernet.encrypt(json.dumps(vault_data).encode())
        with open(SECURE_KEY_VAULT_PATH, "wb") as f:
            f.write(encrypted_vault)
        
        logger.info(f"Stored encryption key for user {user_id[:8]}... in secure vault")
        
    except Exception as e:
        logger.error(f"Failed to store encryption key: {e}")
        raise

def get_encryption_key(user_id: str) -> Optional[str]:
    """Retrieve user's encryption key from secure vault"""
    try:
        master_key = get_master_key()
        fernet = Fernet(master_key)
        
        # Read vault
        with open(SECURE_KEY_VAULT_PATH, "rb") as f:
            encrypted_vault = f.read()
        
        decrypted_vault = fernet.decrypt(encrypted_vault)
        vault_data = json.loads(decrypted_vault.decode())
        
        if user_id not in vault_data["keys"]:
            logger.warning(f"Encryption key not found for user {user_id[:8]}...")
            return None
        
        # Update last accessed
        vault_data["keys"][user_id]["last_accessed"] = datetime.now().isoformat()
        
        # Re-encrypt and store updated vault
        encrypted_vault = fernet.encrypt(json.dumps(vault_data).encode())
        with open(SECURE_KEY_VAULT_PATH, "wb") as f:
            f.write(encrypted_vault)
        
        return vault_data["keys"][user_id]["encryption_key"]
        
    except Exception as e:
        logger.error(f"Failed to retrieve encryption key: {e}")
        return None

def remove_encryption_key(user_id: str) -> bool:
    """Remove user's encryption key from vault (for cleanup)"""
    try:
        master_key = get_master_key()
        fernet = Fernet(master_key)
        
        with open(SECURE_KEY_VAULT_PATH, "rb") as f:
            encrypted_vault = f.read()
        
        decrypted_vault = fernet.decrypt(encrypted_vault)
        vault_data = json.loads(decrypted_vault.decode())
        
        if user_id in vault_data["keys"]:
            del vault_data["keys"][user_id]
            
            encrypted_vault = fernet.encrypt(json.dumps(vault_data).encode())
            with open(SECURE_KEY_VAULT_PATH, "wb") as f:
                f.write(encrypted_vault)
            
            logger.info(f"Removed encryption key for user {user_id[:8]}...")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to remove encryption key: {e}")
        return False

def encrypt_credential(credential: str) -> Tuple[str, str]:
    """Encrypt a credential and return (encrypted_data, encryption_key)"""
    key = Fernet.generate_key()
    fernet = Fernet(key)
    encrypted_data = fernet.encrypt(credential.encode())
    return base64.b64encode(encrypted_data).decode(), base64.b64encode(key).decode()

def decrypt_credential(encrypted_data: str, encryption_key: str) -> str:
    """Decrypt a credential using provided encryption key"""
    key = base64.b64decode(encryption_key.encode())
    fernet = Fernet(key)
    encrypted_bytes = base64.b64decode(encrypted_data.encode())
    return fernet.decrypt(encrypted_bytes).decode()

def secure_decrypt_credential(user_id: str, encrypted_data: str) -> str:
    """Decrypt a credential using key from secure vault"""
    encryption_key = get_encryption_key(user_id)
    if not encryption_key:
        raise Exception(f"Encryption key not found for user {user_id}")
    
    return decrypt_credential(encrypted_data, encryption_key) 