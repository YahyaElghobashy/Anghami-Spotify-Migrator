"""
Module: User Management Routes
Purpose: Complete user setup, login, session management, and credentials handling
Contains: create_user, login_user, validate_session, get_user_credentials, logout_user, delete_user, list_users
"""

import sqlite3
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from ...core.config import USER_CREDENTIALS_DB, SESSION_EXPIRY_DAYS
from ...core.logging import get_logger
from ...models.user_models import UserSetupRequest, UserSession
from ...security.authentication import generate_user_id, generate_session_token
from ...security.encryption import encrypt_credential, store_encryption_key, remove_encryption_key, secure_decrypt_credential

logger = get_logger(__name__)
router = APIRouter(prefix="/setup", tags=["user-management"])

@router.post("/create-user")
async def create_user(request: UserSetupRequest):
    """Create a new user with Spotify credentials"""
    try:
        # Validate Spotify credentials format
        if not request.spotify_client_id or not request.spotify_client_secret:
            return {"success": False, "error": "Spotify credentials are required"}
        
        if len(request.spotify_client_id) != 32:
            return {"success": False, "error": "Invalid Spotify Client ID format"}
        
        if len(request.spotify_client_secret) != 32:
            return {"success": False, "error": "Invalid Spotify Client Secret format"}
        
        # Generate user ID and encrypt credentials
        user_id = generate_user_id()
        display_name = request.display_name or f"User {user_id[:8]}"
        
        encrypted_secret, encryption_key = encrypt_credential(request.spotify_client_secret)
        
        # Store encryption key in secure vault (NOT in database)
        store_encryption_key(user_id, encryption_key)
        
        # Store user data in database (without encryption key)
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO users (user_id, username, display_name, spotify_client_id, 
                              spotify_client_secret, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, request.display_name or f"user_{user_id[:8]}", display_name, request.spotify_client_id, 
              encrypted_secret, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # Create session token
        session_token = generate_session_token()
        
        # Store session
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (session_token, user_id, expires_at)
            VALUES (?, ?, ?)
        ''', (session_token, user_id, (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Created new user: {user_id} ({display_name}) with secure key vault")
        
        return {
            "success": True,
            "session": UserSession(
                user_id=user_id,
                session_token=session_token,
                display_name=display_name,
                spotify_client_id=request.spotify_client_id,
                created_at=datetime.now().isoformat()
            )
        }
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return {"success": False, "error": "Failed to create user account"}

@router.post("/login")
async def login_user(request: dict):
    """Login with existing user credentials"""
    try:
        user_id = request.get("user_id")
        if not user_id:
            return {"success": False, "error": "User ID is required"}
        
        # Get user from database
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, display_name, spotify_client_id, last_used
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        if not user_data:
            conn.close()
            return {"success": False, "error": "User not found"}
        
        # Update last used
        cursor.execute('''
            UPDATE users SET last_used = ? WHERE user_id = ?
        ''', (datetime.now().isoformat(), user_id))
        
        # Create new session
        session_token = generate_session_token()
        cursor.execute('''
            INSERT INTO user_sessions (session_token, user_id, expires_at)
            VALUES (?, ?, ?)
        ''', (session_token, user_id, (datetime.now() + timedelta(days=SESSION_EXPIRY_DAYS)).isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "session": UserSession(
                user_id=user_data[0],
                session_token=session_token,
                display_name=user_data[1],
                spotify_client_id=user_data[2],
                created_at=datetime.now().isoformat()
            )
        }
        
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        return {"success": False, "error": "Login failed"}

@router.get("/session/{session_token}")
async def validate_session(session_token: str):
    """Validate and get user session"""
    try:
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT s.user_id, u.display_name, u.spotify_client_id, s.created_at
            FROM user_sessions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.session_token = ?
        ''', (session_token,))
        
        session_data = cursor.fetchone()
        conn.close()
        
        if not session_data:
            return {"valid": False, "error": "Invalid session"}
        
        return {
            "valid": True,
            "session": UserSession(
                user_id=session_data[0],
                session_token=session_token,
                display_name=session_data[1],
                spotify_client_id=session_data[2],
                created_at=session_data[3]
            )
        }
        
    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return {"valid": False, "error": "Session validation failed"}

@router.get("/user/{user_id}/credentials")
async def get_user_credentials(user_id: str):
    """Get user's Spotify credentials for OAuth"""
    try:
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_client_id, spotify_client_secret
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        cred_data = cursor.fetchone()
        conn.close()
        
        if not cred_data:
            return {"success": False, "error": "User credentials not found"}
        
        # Decrypt the secret using secure vault
        try:
            decrypted_secret = secure_decrypt_credential(user_id, cred_data[1])
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for user {user_id}: {e}")
            return {"success": False, "error": "Failed to decrypt credentials"}
        
        return {
            "success": True,
            "credentials": {
                "client_id": cred_data[0],  # Already plaintext
                "client_secret": decrypted_secret  # Decrypted from vault
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user credentials: {e}")
        return {"success": False, "error": "Failed to retrieve credentials"}

@router.post("/logout")
async def logout_user(request: dict):
    """Logout user and invalidate session"""
    try:
        session_token = request.get("session_token")
        if not session_token:
            return {"success": False, "error": "Session token required"}
        
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM user_sessions 
            WHERE session_token = ?
        ''', (session_token,))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Error logging out user: {e}")
        return {"success": False, "error": "Logout failed"}

@router.delete("/user/{user_id}")
async def delete_user(user_id: str):
    """Delete user and their encryption key from vault"""
    try:
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        # Delete user from database
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_sessions WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        # Remove encryption key from secure vault
        removed = remove_encryption_key(user_id)
        
        if removed:
            logger.info(f"User {user_id[:8]}... deleted from database and key vault")
            return {"success": True, "message": "User deleted successfully"}
        else:
            logger.warning(f"User {user_id[:8]}... deleted from database but key not found in vault")
            return {"success": True, "message": "User deleted (key not found in vault)"}
        
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return {"success": False, "error": "Failed to delete user"}

@router.get("/users")
async def list_users():
    """List all users for login selection (dev/admin only)"""
    try:
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, display_name, spotify_client_id, created_at, last_used,
                   spotify_verified, spotify_profile_data, last_verification
            FROM users
            ORDER BY last_used DESC, created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            # Parse Spotify profile data if available
            spotify_profile = None
            if row[6]:  # spotify_profile_data
                try:
                    spotify_profile = json.loads(row[6])
                except:
                    spotify_profile = None
            
            users.append({
                "user_id": row[0],
                "display_name": row[1],
                "spotify_client_id": row[2],
                "has_credentials": True,
                "created_at": row[3],
                "last_used": row[4],
                "spotify_verified": bool(row[5]) if row[5] is not None else False,
                "spotify_profile": spotify_profile,
                "last_verification": row[7]
            })
        
        conn.close()
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return {"users": []} 