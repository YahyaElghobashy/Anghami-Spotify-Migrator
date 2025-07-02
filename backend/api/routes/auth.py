"""
Module: Auth Routes
Purpose: Basic authentication endpoints (non-OAuth)
Contains: start_spotify_auth, get_auth_status, handle_auth_callback
"""

from datetime import datetime, timedelta
from fastapi import APIRouter
from ...core.logging import get_logger
from ...models.migration_models import AuthStatus

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

# Global auth status
auth_status = AuthStatus(authenticated=False)

@router.post("/spotify")
async def start_spotify_auth():
    """Initiate Spotify OAuth flow"""
    # In a real implementation, this would generate an actual OAuth URL
    auth_url = "https://accounts.spotify.com/authorize?client_id=demo&response_type=code&redirect_uri=http://localhost:3000/callback&scope=playlist-modify-public"
    
    logger.info("Starting Spotify authentication flow")
    return {"authUrl": auth_url}

@router.get("/status")
async def get_auth_status():
    """Get current authentication status"""
    return auth_status

@router.post("/callback")
async def handle_auth_callback(data: dict):
    """Handle OAuth callback"""
    global auth_status
    
    # Simulate successful authentication
    auth_status = AuthStatus(
        authenticated=True,
        user={
            "id": "spotify_user_123",
            "name": "Demo User",
            "email": "demo@example.com"
        },
        expiresAt=(datetime.now() + timedelta(hours=1)).isoformat()
    )
    
    logger.info("User authenticated successfully")
    return auth_status 