"""
Module: Core Configuration
Purpose: Centralized configuration, constants, and settings
Contains: Configuration classes, constants, directory setup functions
"""

import os
from pathlib import Path
from datetime import datetime, timedelta

# Security Configuration
SECURE_KEY_VAULT_PATH = "data/.keyvault"
DATA_DIR = Path("data")

# FastAPI Configuration
API_TITLE = "Anghami → Spotify Migration API"
API_DESCRIPTION = "Backend API for playlist migration from Anghami to Spotify"
API_VERSION = "1.0.0"

# CORS Configuration
ALLOWED_ORIGINS = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000"
]

# Database Configuration
PROFILE_HISTORY_DB = "data/profile_history.db"
USER_CREDENTIALS_DB = "data/user_credentials.db"

# OAuth Configuration
DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Session Configuration
SESSION_EXPIRY_DAYS = 7
AUTH_EXPIRY_HOURS = 24

def ensure_data_directory():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(exist_ok=True)
    
    # Create .gitignore for data directory if it doesn't exist
    gitignore_path = DATA_DIR / ".gitignore"
    if not gitignore_path.exists():
        with open(gitignore_path, "w") as f:
            f.write("""# Ignore all sensitive data files
*.db
.keyvault
*.log
temp/
screenshots/
""") 