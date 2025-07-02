"""
Module: Spotify Service
Purpose: Complete Spotify API integration for OAuth, verification, and data retrieval
Contains: OAuth URLs, token management, profile fetching, credential verification, playlist access
"""

import sqlite3
import json
import base64
import secrets
import requests
from typing import Tuple, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode
from ..core.config import USER_CREDENTIALS_DB, DEFAULT_REDIRECT_URI
from ..core.logging import get_logger
from ..models.spotify_models import SpotifyTokens, SpotifyFullProfile

logger = get_logger(__name__)

# Spotify API Configuration
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

# Required OAuth scopes for the application
SPOTIFY_SCOPES = [
    "user-read-private", 
    "user-read-email", 
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-read-recently-played"
]

async def get_spotify_oauth_url(client_id: str, redirect_uri: str, user_id: str) -> str:
    """Generate Spotify OAuth authorization URL"""
    # Create state parameter with user ID for security
    state = base64.b64encode(f"{user_id}:{secrets.token_urlsafe(16)}".encode()).decode()
    
    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SPOTIFY_SCOPES),
        "state": state,
        "show_dialog": "true"  # Force user to approve each time
    }
    
    oauth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Generated OAuth URL for user {user_id}")
    return oauth_url

async def exchange_spotify_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str) -> Tuple[bool, Optional[SpotifyTokens], Optional[str]]:
    """Exchange authorization code for access tokens"""
    try:
        # Encode credentials for basic auth
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            return False, None, f"Token exchange failed: {response.status_code}"
        
        token_data = response.json()
        
        # Calculate expiration time
        expires_in = token_data.get("expires_in", 3600)
        expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        
        tokens = SpotifyTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", ""),
            expires_at=expires_at,
            scope=token_data.get("scope", "")
        )
        
        return True, tokens, None
        
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {e}")
        return False, None, str(e)

async def get_spotify_user_profile(access_token: str) -> Tuple[bool, Optional[SpotifyFullProfile], Optional[str]]:
    """Get real Spotify user profile data"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get user profile
        profile_response = requests.get(
            f"{SPOTIFY_API_BASE}/me",
            headers=headers,
            timeout=10
        )
        
        if profile_response.status_code != 200:
            logger.error(f"Profile fetch failed: {profile_response.status_code}")
            return False, None, f"Profile fetch failed: {profile_response.status_code}"
        
        profile_data = profile_response.json()
        
        # Get user's playlists count
        playlists_response = requests.get(
            f"{SPOTIFY_API_BASE}/me/playlists?limit=1",
            headers=headers,
            timeout=10
        )
        
        total_playlists = 0
        if playlists_response.status_code == 200:
            playlists_data = playlists_response.json()
            total_playlists = playlists_data.get("total", 0)
        
        # Get following count
        following_response = requests.get(
            f"{SPOTIFY_API_BASE}/me/following?type=artist&limit=1",
            headers=headers,
            timeout=10
        )
        
        total_following = 0
        if following_response.status_code == 200:
            following_data = following_response.json()
            total_following = following_data.get("artists", {}).get("total", 0)
        
        # Create profile object
        spotify_profile = SpotifyFullProfile(
            spotify_id=profile_data["id"],
            display_name=profile_data["display_name"] or profile_data["id"],
            email=profile_data.get("email"),
            avatar_url=profile_data.get("images", [{}])[0].get("url") if profile_data.get("images") else None,
            follower_count=profile_data.get("followers", {}).get("total", 0),
            country=profile_data.get("country"),
            subscription_type=profile_data.get("product", "free").title(),
            verified=True,
            total_public_playlists=total_playlists,
            total_following=total_following,
            connection_status="active",
            last_activity=datetime.now().isoformat(),
            oauth_scopes=SPOTIFY_SCOPES
        )
        
        return True, spotify_profile, None
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return False, None, str(e)

async def verify_spotify_credentials(client_id: str, client_secret: str) -> Tuple[bool, Optional[SpotifyFullProfile], Optional[str]]:
    """Verify Spotify credentials using client credentials flow"""
    try:
        # Encode credentials for basic auth
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            return False, None, f"Invalid Spotify credentials: {response.status_code}"
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return False, None, "No access token received from Spotify"
        
        # Test API call to verify credentials work
        test_url = f"{SPOTIFY_API_BASE}/search"
        test_headers = {"Authorization": f"Bearer {access_token}"}
        test_params = {"q": "test", "type": "track", "limit": 1}
        
        test_response = requests.get(test_url, headers=test_headers, params=test_params, timeout=10)
        
        if test_response.status_code == 200:
            # Create a basic profile for client credentials verification
            spotify_profile = SpotifyFullProfile(
                spotify_id=client_id,
                display_name="Spotify Developer Account",
                verified=True,
                subscription_type="Developer",
                connection_status="verified"
            )
            return True, spotify_profile, None
        else:
            return False, None, "Spotify credentials appear invalid"
            
    except Exception as e:
        logger.error(f"Error verifying Spotify credentials: {e}")
        return False, None, f"Verification error: {str(e)}"

async def refresh_spotify_token(client_id: str, client_secret: str, refresh_token: str) -> Tuple[bool, Optional[SpotifyTokens], Optional[str]]:
    """Refresh Spotify access token using refresh token"""
    try:
        # Encode credentials for basic auth
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(SPOTIFY_TOKEN_URL, headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            return False, None, f"Token refresh failed: {response.status_code}"
        
        token_data = response.json()
        
        # Calculate expiration time
        expires_in = token_data.get("expires_in", 3600)
        expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()
        
        tokens = SpotifyTokens(
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token", refresh_token),  # Keep old refresh token if new one not provided
            expires_at=expires_at,
            scope=token_data.get("scope", "")
        )
        
        return True, tokens, None
        
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return False, None, str(e)

async def get_user_spotify_access_token(user_id: str) -> Optional[str]:
    """Helper function to get user's Spotify access token from database"""
    try:
        conn = sqlite3.connect(USER_CREDENTIALS_DB)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_access_token, spotify_token_expires_at, spotify_refresh_token
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[0]:
            logger.warning(f"No Spotify access token found for user {user_id}")
            return None
        
        access_token, expires_at, refresh_token = result
        
        # Check if token is expired (simplified check)
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(expires_at)
                if datetime.now() >= expires_datetime:
                    logger.info(f"Spotify token expired for user {user_id}, refresh needed")
                    # TODO: Implement token refresh logic
                    return None
            except:
                pass
        
        return access_token
        
    except Exception as e:
        logger.error(f"Error getting Spotify access token: {e}")
        return None

async def get_spotify_playlists_internal(user_id: str, type: str = "all", include_tracks: bool = False, page: int = 1, limit: int = 20):
    """Internal function to get Spotify playlists"""
    try:
        logger.info(f"🎵 Getting Spotify playlists for user: {user_id}, type: {type}")
        
        # For now, return mock playlist data
        mock_playlists = []
        for i in range(5):  # Return 5 mock playlists
            mock_playlists.append({
                "id": f"spotify_playlist_{i+1}",
                "name": f"My Spotify Playlist {i+1}",
                "type": "owned" if i < 3 else "followed",
                "owner_name": f"Owner {i+1}",
                "track_count": 15 + (i * 5),
                "is_public": i % 2 == 0,
                "is_collaborative": False,
                "description": f"Sample Spotify playlist description {i+1}",
                "cover_art_url": None,
                "external_url": f"https://open.spotify.com/playlist/spotify_playlist_{i+1}",
                "total_duration": f"{1 + i}h {20 + (i * 10)}m",
                "follower_count": 100 + (i * 50)
            })
        
        # Apply type filtering
        if type == "owned":
            mock_playlists = [p for p in mock_playlists if p["type"] == "owned"]
        elif type == "followed":
            mock_playlists = [p for p in mock_playlists if p["type"] == "followed"]
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_playlists = mock_playlists[start_idx:end_idx]
        
        return {
            "playlists": paginated_playlists,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(mock_playlists),
                "total_pages": (len(mock_playlists) + limit - 1) // limit,
                "has_next": end_idx < len(mock_playlists),
                "has_prev": page > 1
            },
            "summary": {
                "total_owned": len([p for p in mock_playlists if p["type"] == "owned"]),
                "total_followed": len([p for p in mock_playlists if p["type"] == "followed"]),
                "total_all": len(mock_playlists),
                "filter_applied": type,
                "user_display_name": f"Spotify User {user_id}"
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Spotify playlists: {e}")
        raise Exception(f"Failed to get Spotify playlists: {str(e)}") 