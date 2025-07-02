"""
Module: OAuth Routes
Purpose: Complete Spotify OAuth flow handling with HTML responses and callback processing
Contains: oauth_callback_handler, start_spotify_oauth, handle_spotify_oauth_callback
"""

import sqlite3
import json
import base64
from datetime import datetime
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from ...core.config import USER_CREDENTIALS_DB
from ...core.logging import get_logger
from ...models.spotify_models import SpotifyOAuthRequest
from ...services.spotify_service import (
    get_spotify_oauth_url, 
    exchange_spotify_code_for_tokens,
    get_spotify_user_profile
)
from ...security.encryption import secure_decrypt_credential

logger = get_logger(__name__)
router = APIRouter(tags=["oauth"])

@router.get("/oauth/callback")
async def oauth_callback_handler(code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback from Spotify with HTML response"""
    if error:
        return HTMLResponse(f"""
        <html>
        <head><title>Authorization Failed</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #dc2626;">Authorization Failed</h1>
            <p>Error: {error}</p>
            <p>Please close this window and try again.</p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </body>
        </html>
        """)
    
    if not code or not state:
        return HTMLResponse("""
        <html>
        <head><title>Invalid Request</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #dc2626;">Invalid Request</h1>
            <p>Missing authorization code or state parameter.</p>
            <p>Please close this window and try again.</p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </body>
        </html>
        """)
    
    try:
        # Process the OAuth callback
        result = await handle_spotify_oauth_callback({
            "code": code,
            "state": state,
            "redirect_uri": "http://127.0.0.1:8888/callback"
        })
        
        if result.get("success") and result.get("verified"):
            profile = result.get("spotify_profile", {})
            display_name = profile.get("display_name", "User")
            
            return HTMLResponse(f"""
            <html>
            <head><title>Authorization Successful</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <div style="max-width: 500px; margin: 0 auto;">
                    <h1 style="color: #059669;">✅ Authorization Successful!</h1>
                    <p><strong>Welcome, {display_name}!</strong></p>
                    <p>Your Spotify account has been verified and connected successfully.</p>
                    <div style="background: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #059669; margin-top: 0;">Verification Complete</h3>
                        <p style="margin: 0;">✓ Real-time Spotify connection established</p>
                        <p style="margin: 0;">✓ Profile data synchronized</p>
                        <p style="margin: 0;">✓ Ready for playlist migration</p>
                    </div>
                    <p style="color: #6b7280;">You can now close this window and return to the application.</p>
                </div>
                <script>
                    // Auto-close after 5 seconds
                    setTimeout(() => {{
                        window.close();
                    }}, 5000);
                </script>
            </body>
            </html>
            """)
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return HTMLResponse(f"""
            <html>
            <head><title>Authorization Failed</title></head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: #dc2626;">❌ Authorization Failed</h1>
                <p>Error: {error_msg}</p>
                <p>Please close this window and try again.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
            </body>
            </html>
            """)
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return HTMLResponse(f"""
        <html>
        <head><title>Authorization Error</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #dc2626;">❌ Authorization Error</h1>
            <p>An unexpected error occurred: {str(e)}</p>
            <p>Please close this window and try again.</p>
            <script>setTimeout(() => window.close(), 3000);</script>
        </body>
        </html>
        """)

@router.post("/spotify/oauth/start")
async def start_spotify_oauth(request: SpotifyOAuthRequest):
    """Start Spotify OAuth flow for real user verification"""
    try:
        logger.info(f"Starting Spotify OAuth for user: {request.user_id}")
        
        # Get user credentials
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_client_id, spotify_client_secret
            FROM users WHERE user_id = ?
        ''', (request.user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        client_id, encrypted_secret = user_data
        
        # Generate OAuth URL
        oauth_url = await get_spotify_oauth_url(client_id, request.redirect_uri, request.user_id)
        
        logger.info(f"Generated OAuth URL for user {request.user_id}")
        return {
            "success": True,
            "auth_url": oauth_url,
            "message": "OAuth flow started"
        }
        
    except Exception as e:
        logger.error(f"Error starting OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth: {str(e)}")

@router.post("/spotify/oauth/callback")
async def handle_spotify_oauth_callback(request: dict):
    """Handle Spotify OAuth callback and complete verification"""
    try:
        code = request.get("code")
        state = request.get("state")
        redirect_uri = request.get("redirect_uri", "http://localhost:3000/auth/callback")
        
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing code or state parameter")
        
        # Decode state to get user_id
        try:
            decoded_state = base64.b64decode(state.encode()).decode()
            user_id = decoded_state.split(":")[0]
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid state parameter")
        
        logger.info(f"Processing OAuth callback for user: {user_id}")
        
        # Get user credentials
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_client_id, spotify_client_secret
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        client_id, encrypted_secret = user_data
        client_secret = secure_decrypt_credential(user_id, encrypted_secret)
        
        # Exchange code for tokens
        success, tokens, error = await exchange_spotify_code_for_tokens(
            client_id, client_secret, code, redirect_uri
        )
        
        if not success or not tokens:
            logger.error(f"Token exchange failed for user {user_id}: {error}")
            raise HTTPException(status_code=400, detail=f"Token exchange failed: {error}")
        
        # Get user profile with the access token
        profile_success, spotify_profile, profile_error = await get_spotify_user_profile(tokens.access_token)
        
        if not profile_success or not spotify_profile:
            logger.error(f"Profile fetch failed for user {user_id}: {profile_error}")
            raise HTTPException(status_code=400, detail=f"Profile fetch failed: {profile_error}")
        
        # Store tokens and profile in database
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        # Update user with full verification data
        cursor.execute('''
            UPDATE users 
            SET spotify_verified = ?, 
                spotify_profile_data = ?, 
                spotify_access_token = ?,
                spotify_refresh_token = ?,
                spotify_token_expires_at = ?,
                spotify_token_scope = ?,
                last_verification = ?
            WHERE user_id = ?
        ''', (
            True, 
            json.dumps(spotify_profile.dict()), 
            tokens.access_token,
            tokens.refresh_token,
            tokens.expires_at,
            tokens.scope,
            datetime.now().isoformat(),
            user_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"OAuth verification completed successfully for user: {user_id}")
        return {
            "success": True,
            "verified": True,
            "spotify_profile": spotify_profile,
            "message": "Spotify account verified with OAuth!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth callback failed: {str(e)}") 