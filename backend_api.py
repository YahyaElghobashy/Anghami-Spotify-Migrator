#!/usr/bin/env python3
"""
🎵 Anghami → Spotify Migration Tool - Backend API Server
A FastAPI server that provides all endpoints for the UI to connect to.
"""

import asyncio
import json
import logging
import time
import uuid
import sqlite3
import secrets
import base64
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl

# Import existing extractors (removed unused imports)
# from src.extractors.anghami_direct_extractor import AnghamiDirectExtractor - No longer used
# from src.models.anghami_models import AnghamiPlaylist, AnghamiTrack - Using Pydantic models instead

# Import the improved profile extractor
import sys
sys.path.append(str(Path(__file__).parent / "src" / "extractors"))
from anghami_profile_extractor import AnghamiProfileExtractor
from anghami_user_playlist_discoverer import AnghamiUserPlaylistDiscoverer
from spotify_playlist_extractor import SpotifyPlaylistExtractor

# Import for Spotify API
import requests
from urllib.parse import urlencode

# Import Spotify models
sys.path.append(str(Path(__file__).parent / "src" / "models"))
from spotify_models import SpotifyPlaylist, SpotifyTrack, SpotifyUserPlaylists

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security Configuration
SECURE_KEY_VAULT_PATH = "data/.keyvault"
DATA_DIR = Path("data")

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

def init_secure_key_vault():
    """Initialize secure key vault separated from main database"""
    ensure_data_directory()
    
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

# Initialize FastAPI app
app = FastAPI(
    title="Anghami → Spotify Migration API",
    description="Backend API for playlist migration from Anghami to Spotify",
    version="1.0.0"
)

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_database():
    """Initialize SQLite database for profile history"""
    conn = sqlite3.connect('data/profile_history.db')
    cursor = conn.cursor()
    
    # Create profile history table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_url TEXT UNIQUE NOT NULL,
            display_name TEXT,
            avatar_url TEXT,
            follower_count INTEGER,
            usage_count INTEGER DEFAULT 1,
            last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_database()

# User credential management models
class UserSetupRequest(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
    display_name: Optional[str] = None

class UserCredentials(BaseModel):
    user_id: str
    display_name: str
    spotify_client_id: str
    has_credentials: bool
    created_at: str
    last_used: Optional[str] = None

class UserSession(BaseModel):
    user_id: str
    session_token: str
    display_name: str
    spotify_client_id: str
    created_at: str

# Original data models
class ProfileValidationRequest(BaseModel):
    profile_url: str

class ProfileData(BaseModel):
    profile_url: str
    profile_id: str
    display_name: str
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    most_played_songs: Optional[List[Dict]] = None
    is_valid: bool
    error_message: Optional[str] = None

class ProfileHistoryItem(BaseModel):
    id: int
    profile_url: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    usage_count: int
    last_used: str

class AnghamiTrack(BaseModel):
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[str] = None
    confidence: Optional[float] = None
    spotifyMatch: Optional[Dict] = None

class AnghamiPlaylist(BaseModel):
    id: str
    name: str
    trackCount: int
    duration: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    tracks: Optional[List[AnghamiTrack]] = None

class MigrationRequest(BaseModel):
    playlist_ids: List[str]

class MigrationStatus(BaseModel):
    sessionId: str
    status: str
    progress: float
    currentPlaylist: Optional[str] = None
    totalPlaylists: int
    completedPlaylists: int
    totalTracks: int
    matchedTracks: int
    createdPlaylists: int
    errors: List[str]
    message: Optional[str] = None

class AuthStatus(BaseModel):
    authenticated: bool
    user: Optional[Dict] = None
    expiresAt: Optional[str] = None

# In-memory storage (replace with database in production)
migration_sessions: Dict[str, MigrationStatus] = {}
websocket_connections: Dict[str, WebSocket] = {}
auth_status = AuthStatus(authenticated=False)
current_profile: Optional[ProfileData] = None

# Add new models for Spotify verification
class SpotifyVerificationRequest(BaseModel):
    user_id: str

class SpotifyTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: str
    scope: str

class SpotifyOAuthRequest(BaseModel):
    user_id: str
    redirect_uri: str = "http://127.0.0.1:8888/callback"

class SpotifyRecentlyPlayed(BaseModel):
    track_name: str
    artist_name: str
    album_name: str
    played_at: str
    track_uri: str
    external_url: str

class SpotifyFullProfile(BaseModel):
    spotify_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    country: Optional[str] = None
    subscription_type: Optional[str] = None
    verified: bool = False
    # Enhanced data
    total_public_playlists: Optional[int] = None
    total_following: Optional[int] = None
    recently_played: Optional[List[SpotifyRecentlyPlayed]] = None
    connection_status: str = "active"  # active, expired, invalid
    last_activity: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None

class VerifiedUserSession(BaseModel):
    user_id: str
    session_token: str
    display_name: str
    spotify_client_id: str
    created_at: str
    # New verification fields
    spotify_verified: bool = False
    spotify_profile: Optional[SpotifyFullProfile] = None
    anghami_profile: Optional[ProfileData] = None

# Utility functions
def validate_anghami_profile_url(url: str) -> bool:
    """Validate if URL is a valid Anghami profile URL"""
    try:
        parsed = urlparse(url)
        return (
            parsed.netloc in ['play.anghami.com', 'anghami.com', 'www.anghami.com'] and
            '/profile/' in parsed.path
        )
    except:
        return False

def extract_profile_id(url: str) -> Optional[str]:
    """Extract profile ID from Anghami URL"""
    try:
        parsed = urlparse(url)
        if '/profile/' in parsed.path:
            return parsed.path.split('/profile/')[-1].split('?')[0].split('/')[0]
    except:
        pass
    return None

async def fetch_anghami_profile_data(profile_url: str) -> ProfileData:
    """Fetch profile data from Anghami using the profile extractor"""
    try:
        profile_extractor = AnghamiProfileExtractor()
        
        # Extract real profile data from Anghami
        profile_data = await profile_extractor.extract_profile_data(profile_url)
        
        return ProfileData(
            profile_url=profile_data["profile_url"],
            profile_id=profile_data.get("profile_id", extract_profile_id(profile_url) or "unknown"),
            display_name=profile_data.get("display_name", "Unknown User"),
            avatar_url=profile_data.get("avatar_url"),
            follower_count=profile_data.get("follower_count"),
            most_played_songs=profile_data.get("most_played_songs"),
            is_valid=profile_data.get("is_valid", False),
            error_message=profile_data.get("error_message")
        )
        
    except Exception as e:
        logger.error(f"Error fetching profile data: {e}")
        return ProfileData(
            profile_url=profile_url,
            profile_id=extract_profile_id(profile_url) or "unknown",
            display_name="Unknown User",
            avatar_url=None,
            follower_count=0,
            most_played_songs=[],
            is_valid=False,
            error_message=f"Failed to fetch profile data: {str(e)}"
        )

def store_profile_in_history(profile_data: ProfileData):
    """Store or update profile in history database"""
    conn = sqlite3.connect('data/profile_history.db')
    cursor = conn.cursor()
    
    try:
        # Check if profile already exists
        cursor.execute('SELECT id, usage_count FROM profile_history WHERE profile_url = ?', 
                      (profile_data.profile_url,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing profile
            profile_id, usage_count = existing
            cursor.execute('''
                UPDATE profile_history 
                SET display_name = ?, avatar_url = ?, follower_count = ?, 
                    usage_count = ?, last_used = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (profile_data.display_name, profile_data.avatar_url, 
                  profile_data.follower_count, usage_count + 1, profile_id))
        else:
            # Insert new profile
            cursor.execute('''
                INSERT INTO profile_history 
                (profile_url, display_name, avatar_url, follower_count, usage_count)
                VALUES (?, ?, ?, ?, 1)
            ''', (profile_data.profile_url, profile_data.display_name, 
                  profile_data.avatar_url, profile_data.follower_count))
        
        conn.commit()
    except Exception as e:
        logger.error(f"Error storing profile in history: {e}")
    finally:
        conn.close()

def get_profile_history() -> List[ProfileHistoryItem]:
    """Get profile history from database"""
    conn = sqlite3.connect('data/profile_history.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, profile_url, display_name, avatar_url, follower_count, 
                   usage_count, last_used
            FROM profile_history 
            ORDER BY last_used DESC 
            LIMIT 10
        ''')
        
        rows = cursor.fetchall()
        return [
            ProfileHistoryItem(
                id=row[0],
                profile_url=row[1],
                display_name=row[2],
                avatar_url=row[3],
                follower_count=row[4],
                usage_count=row[5],
                last_used=row[6]
            )
            for row in rows
        ]
    except Exception as e:
        logger.error(f"Error fetching profile history: {e}")
        return []
    finally:
        conn.close()

# API Endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

# Profile Management Endpoints

@app.post("/profiles/validate")
async def validate_anghami_profile(request: ProfileValidationRequest):
    """Validate an Anghami profile URL and extract profile data"""
    try:
        logger.info(f"Validating profile: {request.profile_url}")
        
        # Use the improved profile extractor
        extractor = AnghamiProfileExtractor()
        profile_data = await extractor.extract_profile_data(request.profile_url)
        
        logger.info(f"Profile validation successful for: {profile_data['display_name']}")
        return ProfileData(**profile_data)
        
    except Exception as e:
        logger.error(f"Profile validation failed: {e}")
        return ProfileData(
            profile_url=request.profile_url,
            profile_id="unknown",
            display_name="Unknown User",
            avatar_url=None,
            follower_count=0,
            most_played_songs=[],
            is_valid=False,
            error_message=str(e)
        )

@app.get("/profiles/history")
async def get_profiles_history() -> List[ProfileHistoryItem]:
    """Get profile usage history"""
    return get_profile_history()

@app.post("/profiles/confirm")
async def confirm_profile(request: ProfileValidationRequest) -> ProfileData:
    """Confirm and set current profile"""
    global current_profile, auth_status
    
    # Validate and fetch profile data
    profile_data = await fetch_anghami_profile_data(request.profile_url)
    
    if profile_data.is_valid:
        current_profile = profile_data
        store_profile_in_history(profile_data)
        
        # Set authentication status to true when profile is confirmed
        auth_status = AuthStatus(
            authenticated=True,
            user={
                "id": extract_profile_id(profile_data.profile_url),
                "name": profile_data.display_name or "Anghami User",
                "profile_url": profile_data.profile_url
            },
            expiresAt=(datetime.now() + timedelta(hours=24)).isoformat()
        )
        
        logger.info(f"Confirmed profile: {profile_data.display_name}")
    
    return profile_data

@app.delete("/profiles/{profile_id}")
async def delete_profile_from_history(profile_id: int):
    """Delete profile from history"""
    conn = sqlite3.connect('data/profile_history.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM profile_history WHERE id = ?', (profile_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            logger.info(f"Deleted profile from history: {profile_id}")
            return {"success": True, "message": "Profile deleted from history"}
        else:
            raise HTTPException(status_code=404, detail="Profile not found in history")
    except Exception as e:
        logger.error(f"Error deleting profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete profile")
    finally:
        conn.close()

# Existing endpoints...

@app.post("/auth/spotify")
async def start_spotify_auth():
    """Initiate Spotify OAuth flow"""
    # In a real implementation, this would generate an actual OAuth URL
    auth_url = "https://accounts.spotify.com/authorize?client_id=demo&response_type=code&redirect_uri=http://localhost:3000/callback&scope=playlist-modify-public"
    
    logger.info("Starting Spotify authentication flow")
    return {"authUrl": auth_url}

@app.get("/auth/status")
async def get_auth_status():
    """Get current authentication status"""
    return auth_status

@app.post("/auth/callback")
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

@app.get("/playlists")
async def get_playlists():
    """Get user's real Anghami playlists using playlist discoverer"""
    global current_profile
    
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    try:
        logger.info(f"🎵 Extracting real playlists for profile: {current_profile.display_name}")
        
        # Use the playlist discoverer to get real playlists
        discoverer = AnghamiUserPlaylistDiscoverer()
        user_playlists = await discoverer.discover_user_playlists(current_profile.profile_url)
        
        # Convert discovered playlists to API format
        api_playlists = []
        
        # Add created playlists
        for playlist in user_playlists.created_playlists:
            api_playlist = AnghamiPlaylist(
                id=playlist.id,
                name=f"🎵 {playlist.name}",  # Add created indicator
                trackCount=0,  # Will be filled when individual playlist is requested
                duration="Unknown",
                description=f"Created by {current_profile.display_name}. {playlist.description}".strip(),
                imageUrl=playlist.cover_art_url,
                tracks=[]
            )
            api_playlists.append(api_playlist)
        
        # Add followed playlists
        for playlist in user_playlists.followed_playlists:
            api_playlist = AnghamiPlaylist(
                id=playlist.id,
                name=f"➕ {playlist.name}",  # Add followed indicator
                trackCount=0,  # Will be filled when individual playlist is requested
                duration="Unknown",
                description=f"Followed by {current_profile.display_name}. {playlist.description}".strip(),
                imageUrl=playlist.cover_art_url,
            tracks=[]
            )
            api_playlists.append(api_playlist)
        
        logger.info(f"✅ Returning {len(api_playlists)} real playlists ({user_playlists.total_created} created, {user_playlists.total_followed} followed)")
        return api_playlists
        
    except Exception as e:
        logger.error(f"❌ Error extracting playlists: {e}")
        # Fallback to indicate error
        return [
        AnghamiPlaylist(
                id="error",
                name=f"❌ Error Loading Playlists",
                trackCount=0,
                duration="N/A",
                description=f"Failed to load playlists from {current_profile.display_name}: {str(e)}",
                imageUrl=None,
            tracks=[]
        )
    ]

@app.get("/playlists/{playlist_id}")
async def get_playlist_details(playlist_id: str):
    """Get detailed information about a specific playlist with tracks"""
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    try:
        # First, find the playlist in our discovered playlists
        all_playlists = await get_playlists()
        playlist_summary = next((p for p in all_playlists if p.id == playlist_id), None)
        
        if not playlist_summary:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
        # If it's an error playlist, return it as-is
        if playlist_id == "error":
            return playlist_summary
        
        logger.info(f"🎵 Extracting detailed tracks for playlist: {playlist_summary.name}")
        
        # Use the direct extractor to get full playlist details with tracks
        from anghami_direct_extractor import AnghamiDirectExtractor
        
        direct_extractor = AnghamiDirectExtractor()
        playlist_url = f"https://play.anghami.com/playlist/{playlist_id}"
        
        # Extract full playlist data including tracks
        full_playlist = await direct_extractor.extract_playlist(playlist_url)
        
        # Convert to API format
        api_tracks = []
        for track in full_playlist.tracks:
            api_track = AnghamiTrack(
                id=str(len(api_tracks) + 1),
                title=track.title,
                artist=track.primary_artist,
                album=getattr(track, 'album', 'Unknown Album'),
                duration=getattr(track, 'duration', 'Unknown'),
                confidence=1.0
            )
            api_tracks.append(api_track)
        
        # Create detailed playlist response
        detailed_playlist = AnghamiPlaylist(
            id=playlist_id,
            name=playlist_summary.name,
            trackCount=len(api_tracks),
            duration=getattr(full_playlist, 'duration', f"{len(api_tracks)} tracks"),
            description=playlist_summary.description,
            imageUrl=playlist_summary.imageUrl,
            tracks=api_tracks
        )
        
        logger.info(f"✅ Returning detailed playlist with {len(api_tracks)} tracks")
        return detailed_playlist
        
    except Exception as e:
        logger.error(f"❌ Error extracting playlist details: {e}")
        
        # Return basic playlist info with error indication
        return AnghamiPlaylist(
            id=playlist_id,
            name=f"❌ Error Loading Tracks",
            trackCount=0,
            duration="N/A",
            description=f"Failed to load tracks: {str(e)}",
            imageUrl=None,
            tracks=[]
        )

# New C.1 API Endpoints for Enhanced Playlist Access

@app.get("/anghami/playlists")
async def get_anghami_playlists(
    profile_url: str = None,
    type: str = "all",  # all, created, followed
    page: int = 1,
    limit: int = 20
):
    """Enhanced playlist endpoint with filtering and pagination"""
    # Use current profile if no profile_url provided
    target_profile_url = profile_url or (current_profile.profile_url if current_profile else None)
    
    if not target_profile_url:
        raise HTTPException(status_code=400, detail="No profile URL provided and no current profile selected")
    
    try:
        logger.info(f"🎵 Getting Anghami playlists: type={type}, page={page}, limit={limit}")
        
        discoverer = AnghamiUserPlaylistDiscoverer()
        user_playlists = await discoverer.discover_user_playlists(target_profile_url)
        
        # Filter by type
        filtered_playlists = []
        if type in ["all", "created"]:
            filtered_playlists.extend(user_playlists.created_playlists)
        if type in ["all", "followed"]:
            filtered_playlists.extend(user_playlists.followed_playlists)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_playlists = filtered_playlists[start_idx:end_idx]
        
        # Convert to API format
        api_playlists = []
        for playlist in paginated_playlists:
            indicator = "🎵" if playlist.playlist_type == "created" else "➕"
            api_playlist = {
                "id": playlist.id,
                "name": f"{indicator} {playlist.name}",
                "type": playlist.playlist_type,
                "url": playlist.url,
                "description": playlist.description,
                "cover_art_url": playlist.cover_art_url
            }
            api_playlists.append(api_playlist)
        
        return {
            "playlists": api_playlists,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_playlists),
                "total_pages": (len(filtered_playlists) + limit - 1) // limit,
                "has_next": end_idx < len(filtered_playlists),
                "has_prev": page > 1
            },
            "summary": {
                "total_created": user_playlists.total_created,
                "total_followed": user_playlists.total_followed,
                "total_all": user_playlists.total_created + user_playlists.total_followed,
                "filter_applied": type
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Anghami playlists: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playlists: {str(e)}")

@app.get("/anghami/playlists/summary")
async def get_anghami_playlists_summary(profile_url: str = None):
    """Get summary of playlist counts by type"""
    target_profile_url = profile_url or (current_profile.profile_url if current_profile else None)
    
    if not target_profile_url:
        raise HTTPException(status_code=400, detail="No profile URL provided and no current profile selected")
    
    try:
        logger.info(f"📊 Getting playlist summary for profile")
        
        discoverer = AnghamiUserPlaylistDiscoverer()
        user_playlists = await discoverer.discover_user_playlists(target_profile_url)
        
        return {
            "profile_url": target_profile_url,
            "user_id": user_playlists.user_id,
            "created_playlists": user_playlists.total_created,
            "followed_playlists": user_playlists.total_followed,
            "total_playlists": user_playlists.total_created + user_playlists.total_followed,
            "extraction_timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting playlist summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playlist summary: {str(e)}")

# C.2 - Spotify Playlist Retrieval System API Endpoints

@app.get("/spotify/playlists/{user_id}")
async def get_spotify_playlists(
    user_id: str,
    type: str = "all",  # all, owned, followed
    include_tracks: bool = False,
    page: int = 1,
    limit: int = 20
):
    """Get user's Spotify playlists with filtering and pagination"""
    try:
        logger.info(f"🎵 Getting Spotify playlists for user: {user_id}, type: {type}")
        
        # Get user's Spotify access token from database
        access_token = await get_user_spotify_access_token(user_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Spotify access token not found. Please re-authenticate.")
        
        # Create extractor and set token
        extractor = SpotifyPlaylistExtractor()
        extractor.set_access_token(access_token)
        
        # Extract playlists (always use "me" for authenticated user)
        user_playlists = await extractor.extract_user_playlists(
            user_id="me",
            include_followed=(type in ["all", "followed"]),
            include_tracks=include_tracks
        )
        
        # Filter by type
        filtered_playlists = []
        if type in ["all", "owned"]:
            filtered_playlists.extend(user_playlists.owned_playlists)
        if type in ["all", "followed"]:
            filtered_playlists.extend(user_playlists.followed_playlists)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_playlists = filtered_playlists[start_idx:end_idx]
        
        # Convert to API format
        api_playlists = []
        for playlist in paginated_playlists:
            indicator = "🎵" if playlist.is_owned else "➕"
            api_playlist = {
                "id": playlist.id,
                "name": f"{indicator} {playlist.name}",
                "type": "owned" if playlist.is_owned else "followed",
                "owner_name": playlist.owner_name,
                "track_count": playlist.track_count,
                "is_public": playlist.is_public,
                "is_collaborative": playlist.is_collaborative,
                "description": playlist.description,
                "cover_art_url": playlist.cover_art_url,
                "external_url": playlist.external_url,
                "total_duration": playlist.total_duration_formatted,
                "follower_count": playlist.follower_count
            }
            
            # Include tracks if requested and available
            if include_tracks and playlist.tracks:
                api_playlist["tracks"] = [
                    {
                        "id": track.id,
                        "title": track.title,
                        "artists": track.artists,
                        "album": track.album,
                        "duration": track.duration_formatted,
                        "external_url": track.external_url,
                        "added_at": track.added_at
                    }
                    for track in playlist.tracks
                ]
            
            api_playlists.append(api_playlist)
        
        return {
            "playlists": api_playlists,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_playlists),
                "total_pages": (len(filtered_playlists) + limit - 1) // limit,
                "has_next": end_idx < len(filtered_playlists),
                "has_prev": page > 1
            },
            "summary": {
                "total_owned": user_playlists.total_owned,
                "total_followed": user_playlists.total_followed,
                "total_all": user_playlists.total_playlists,
                "filter_applied": type,
                "user_display_name": user_playlists.display_name
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Spotify playlists: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get Spotify playlists: {str(e)}")

@app.get("/spotify/playlists/{playlist_id}/details")
async def get_spotify_playlist_details(playlist_id: str, user_id: str = None):
    """Get detailed information about a specific Spotify playlist"""
    try:
        logger.info(f"🎵 Getting Spotify playlist details: {playlist_id}")
        
        # Get user's Spotify access token
        if not user_id:
            # Try to get from current session or default to a stored token
            user_id = "current"  # This should be replaced with actual user context
        
        access_token = await get_user_spotify_access_token(user_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Spotify access token not found. Please re-authenticate.")
        
        # Create extractor and get playlist details
        extractor = SpotifyPlaylistExtractor()
        extractor.set_access_token(access_token)
        
        playlist = await extractor.extract_playlist_details(playlist_id, include_tracks=True)
        
        # Convert to API format
        return {
            "id": playlist.id,
            "name": playlist.name,
            "description": playlist.description,
            "owner_id": playlist.owner_id,
            "owner_name": playlist.owner_name,
            "is_owned": playlist.is_owned,
            "is_followed": playlist.is_followed,
            "is_public": playlist.is_public,
            "is_collaborative": playlist.is_collaborative,
            "track_count": playlist.track_count,
            "total_duration": playlist.total_duration_formatted,
            "follower_count": playlist.follower_count,
            "cover_art_url": playlist.cover_art_url,
            "external_url": playlist.external_url,
            "tracks": [
                {
                    "id": track.id,
                    "title": track.title,
                    "artists": track.artists,
                    "album": track.album,
                    "duration": track.duration_formatted,
                    "duration_ms": track.duration_ms,
                    "preview_url": track.preview_url,
                    "external_url": track.external_url,
                    "explicit": track.explicit,
                    "popularity": track.popularity,
                    "added_at": track.added_at,
                    "added_by": track.added_by
                }
                for track in playlist.tracks
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Spotify playlist details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playlist details: {str(e)}")

@app.get("/spotify/playlists/{playlist_id}/tracks")
async def get_spotify_playlist_tracks(playlist_id: str, user_id: str = None):
    """Get tracks from a specific Spotify playlist"""
    try:
        logger.info(f"🎵 Getting tracks for Spotify playlist: {playlist_id}")
        
        # Get user's Spotify access token
        if not user_id:
            user_id = "current"
        
        access_token = await get_user_spotify_access_token(user_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Spotify access token not found.")
        
        # Create extractor and get tracks
        extractor = SpotifyPlaylistExtractor()
        extractor.set_access_token(access_token)
        
        tracks = await extractor._get_playlist_tracks(playlist_id)
        
        return {
            "playlist_id": playlist_id,
            "track_count": len(tracks),
            "tracks": [
                {
                    "id": track.id,
                    "title": track.title,
                    "artists": track.artists,
                    "album": track.album,
                    "duration": track.duration_formatted,
                    "external_url": track.external_url,
                    "added_at": track.added_at
                }
                for track in tracks
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Spotify playlist tracks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playlist tracks: {str(e)}")

@app.post("/spotify/playlists/batch-details")
async def get_spotify_playlists_batch_details(request: dict):
    """Get detailed information for multiple Spotify playlists"""
    playlist_ids = request.get("playlist_ids", [])
    user_id = request.get("user_id", "current")
    include_tracks = request.get("include_tracks", False)
    
    try:
        logger.info(f"🎵 Getting batch details for {len(playlist_ids)} Spotify playlists")
        
        access_token = await get_user_spotify_access_token(user_id)
        if not access_token:
            raise HTTPException(status_code=401, detail="Spotify access token not found.")
        
        extractor = SpotifyPlaylistExtractor()
        extractor.set_access_token(access_token)
        
        playlists = []
        for playlist_id in playlist_ids:
            try:
                playlist = await extractor.extract_playlist_details(playlist_id, include_tracks=include_tracks)
                playlists.append(playlist.to_dict())
            except Exception as e:
                logger.warning(f"Failed to get details for playlist {playlist_id}: {e}")
                continue
        
        return {
            "requested_count": len(playlist_ids),
            "retrieved_count": len(playlists),
            "playlists": playlists
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting batch playlist details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get batch playlist details: {str(e)}")

async def get_user_spotify_access_token(user_id: str) -> Optional[str]:
    """Helper function to get user's Spotify access token from database"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
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
                from datetime import datetime
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

@app.post("/migrate")
async def start_migration(request: MigrationRequest):
    """Start playlist migration"""
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    session_id = str(uuid.uuid4())
    
    # Get sample playlists for migration
    sample_playlists = await get_playlists()
    selected_playlists = [p for p in sample_playlists if p.id in request.playlist_ids]
    
    # Initialize migration status
    migration_status = MigrationStatus(
        sessionId=session_id,
        status="extracting",
        progress=0.0,
        totalPlaylists=len(request.playlist_ids),
        completedPlaylists=0,
        totalTracks=sum(p.trackCount for p in selected_playlists),
        matchedTracks=0,
        createdPlaylists=0,
        errors=[],
        message=f"Starting playlist extraction from {current_profile.display_name}'s Anghami profile..."
    )
    
    migration_sessions[session_id] = migration_status
    
    # Start background migration task
    asyncio.create_task(simulate_migration(session_id, request.playlist_ids))
    
    logger.info(f"Started migration session: {session_id} for profile: {current_profile.display_name}")
    return {"sessionId": session_id}

@app.get("/migrate/status/{session_id}")
async def get_migration_status(session_id: str):
    """Get migration status"""
    if session_id not in migration_sessions:
        raise HTTPException(status_code=404, detail="Migration session not found")
    
    return migration_sessions[session_id]

@app.post("/migrate/{session_id}/stop")
async def stop_migration(session_id: str):
    """Stop migration"""
    if session_id not in migration_sessions:
        raise HTTPException(status_code=404, detail="Migration session not found")
    
    migration_sessions[session_id].status = "stopped"
    migration_sessions[session_id].message = "Migration stopped by user"
    
    logger.info(f"Stopped migration session: {session_id}")
    return {"success": True}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time migration updates"""
    await websocket.accept()
    websocket_connections[session_id] = websocket
    
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Send current status
            if session_id in migration_sessions:
                await websocket.send_json(migration_sessions[session_id].dict())
            
            # Check if migration is complete
            if (session_id in migration_sessions and 
                migration_sessions[session_id].status in ["completed", "error", "stopped"]):
                break
                
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
    finally:
        if session_id in websocket_connections:
            del websocket_connections[session_id]

# Background Tasks

async def simulate_migration(session_id: str, playlist_ids: List[str]):
    """Simulate the migration process with realistic progress updates"""
    if session_id not in migration_sessions:
        return
    
    status = migration_sessions[session_id]
    selected_playlists = await get_playlists()
    selected_playlists = [p for p in selected_playlists if p.id in playlist_ids]
    
    try:
        # Phase 1: Extraction (0-25%)
        status.status = "extracting"
        status.message = f"Extracting playlists from {current_profile.display_name if current_profile else 'Anghami'}..."
        
        for i, playlist in enumerate(selected_playlists):
            status.progress = (i / len(selected_playlists)) * 25
            status.currentPlaylist = playlist.name
            status.message = f"Extracting: {playlist.name}"
            await asyncio.sleep(2)  # Simulate extraction time
        
        # Phase 2: Matching (25-75%)
        status.status = "matching"
        status.message = "Matching tracks with Spotify..."
        
        total_tracks = sum(p.trackCount for p in selected_playlists)
        matched_count = 0
        
        for playlist in selected_playlists:
            status.currentPlaylist = playlist.name
            
            for track_num in range(playlist.trackCount):
                matched_count += 1
                status.matchedTracks = matched_count
                status.progress = 25 + (matched_count / total_tracks) * 50
                status.message = f"Matching tracks in: {playlist.name} ({track_num + 1}/{playlist.trackCount})"
                
                # Simulate some tracks that need review (Arabic tracks)
                if "Arabic" in playlist.name or "موسى" in getattr(playlist.tracks[0] if playlist.tracks else None, 'artist', ''):
                    status.message += " - Reviewing Arabic track match"
                
                await asyncio.sleep(0.5)  # Simulate matching time
        
        # Phase 3: Creating (75-100%)
        status.status = "creating"
        status.message = "Creating playlists in Spotify..."
        
        for i, playlist in enumerate(selected_playlists):
            status.currentPlaylist = playlist.name
            status.progress = 75 + ((i + 1) / len(selected_playlists)) * 25
            status.message = f"Creating Spotify playlist: {playlist.name}"
            status.completedPlaylists = i + 1
            status.createdPlaylists = i + 1
            await asyncio.sleep(3)  # Simulate playlist creation time
        
        # Complete
        status.status = "completed"
        status.progress = 100.0
        status.message = f"Successfully migrated {len(selected_playlists)} playlists!"
        status.currentPlaylist = None
        
        logger.info(f"Migration completed for session: {session_id}")
        
    except Exception as e:
        status.status = "error"
        status.errors.append(str(e))
        status.message = f"Migration failed: {str(e)}"
        logger.error(f"Migration failed for session {session_id}: {e}")

# User credential management functions
def init_user_database():
    """Initialize the user credential database with proper schema"""
    try:
        ensure_data_directory()
        
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        # Create users table with all required fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                display_name TEXT NOT NULL,
                spotify_client_id TEXT NOT NULL,
                spotify_client_secret TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT,
                
                -- Enhanced Spotify verification fields
                spotify_verified BOOLEAN DEFAULT FALSE,
                spotify_profile_data TEXT,
                last_verification TEXT,
                
                -- OAuth token fields
                spotify_access_token TEXT,
                spotify_refresh_token TEXT,
                spotify_token_expires_at TEXT,
                spotify_token_scope TEXT
            )
        ''')
        
        # Create user sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Check if we need to add new columns to existing tables
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add missing OAuth token columns if they don't exist
        new_columns = [
            ("spotify_access_token", "TEXT"),
            ("spotify_refresh_token", "TEXT"), 
            ("spotify_token_expires_at", "TEXT"),
            ("spotify_token_scope", "TEXT")
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}')
                logger.info(f"Added new column '{column_name}' to users table")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ User database initialized successfully with OAuth support")
        
    except Exception as e:
        logger.error(f"❌ Error initializing user database: {e}")
        raise

def encrypt_credential(credential: str) -> tuple[str, str]:
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

def generate_user_id() -> str:
    """Generate a unique user ID"""
    return secrets.token_urlsafe(16)

def generate_session_token() -> str:
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

@app.on_event("startup")
async def startup():
    init_database()
    init_secure_key_vault()  # Initialize secure key vault first
    init_user_database()  # Initialize user credential system

@app.post("/setup/create-user")
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
        conn = sqlite3.connect('data/user_credentials.db')
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
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_sessions (session_token, user_id, expires_at)
            VALUES (?, ?, ?)
        ''', (session_token, user_id, (datetime.now() + timedelta(days=7)).isoformat()))
        
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

@app.post("/setup/login")
async def login_user(request: dict):
    """Login with existing user credentials"""
    try:
        user_id = request.get("user_id")
        if not user_id:
            return {"success": False, "error": "User ID is required"}
        
        # Get user from database
        conn = sqlite3.connect('data/user_credentials.db')
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
        ''', (session_token, user_id, (datetime.now() + timedelta(days=7)).isoformat()))
        
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

@app.get("/setup/session/{session_token}")
async def validate_session(session_token: str):
    """Validate and get user session"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
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

@app.get("/setup/user/{user_id}/credentials")
async def get_user_credentials(user_id: str):
    """Get user's Spotify credentials for OAuth"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
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

@app.post("/setup/logout")
async def logout_user(request: dict):
    """Logout user and invalidate session"""
    try:
        session_token = request.get("session_token")
        if not session_token:
            return {"success": False, "error": "Session token required"}
        
        conn = sqlite3.connect('data/user_credentials.db')
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

@app.delete("/setup/user/{user_id}")
async def delete_user(user_id: str):
    """Delete user and their encryption key from vault"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
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

@app.get("/setup/users")
async def list_users():
    """List all users for login selection (dev/admin only)"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
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

# OAuth Callback Handler
@app.get("/oauth/callback")
async def oauth_callback_handler(code: str = None, state: str = None, error: str = None):
    """Handle OAuth callback from Spotify"""
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

# OAuth Helper Functions
async def get_spotify_oauth_url(client_id: str, redirect_uri: str, user_id: str) -> str:
    """Generate Spotify OAuth authorization URL"""
    try:
        # Encode state with user_id for callback
        state = base64.b64encode(f"{user_id}:{secrets.token_urlsafe(16)}".encode()).decode()
        
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": "user-read-private user-read-email user-read-recently-played user-top-read playlist-read-private",
            "state": state,
            "show_dialog": "true"  # Force user to see authorization dialog
        }
        
        oauth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
        return oauth_url
        
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        raise Exception(f"Failed to generate OAuth URL: {str(e)}")

async def exchange_spotify_code_for_tokens(client_id: str, client_secret: str, code: str, redirect_uri: str) -> tuple[bool, Optional[SpotifyTokens], Optional[str]]:
    """Exchange authorization code for access tokens"""
    try:
        auth_url = "https://accounts.spotify.com/api/token"
        
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
        
        response = requests.post(auth_url, headers=headers, data=data, timeout=10)
        
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

async def get_spotify_user_profile(access_token: str) -> tuple[bool, Optional[SpotifyFullProfile], Optional[str]]:
    """Get real Spotify user profile data"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get user profile
        profile_response = requests.get(
            "https://api.spotify.com/v1/me",
            headers=headers,
            timeout=10
        )
        
        if profile_response.status_code != 200:
            logger.error(f"Profile fetch failed: {profile_response.status_code}")
            return False, None, f"Profile fetch failed: {profile_response.status_code}"
        
        profile_data = profile_response.json()
        
        # Get user's playlists count
        playlists_response = requests.get(
            "https://api.spotify.com/v1/me/playlists?limit=1",
            headers=headers,
            timeout=10
        )
        
        total_playlists = 0
        if playlists_response.status_code == 200:
            playlists_data = playlists_response.json()
            total_playlists = playlists_data.get("total", 0)
        
        # Get following count
        following_response = requests.get(
            "https://api.spotify.com/v1/me/following?type=artist&limit=1",
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
            oauth_scopes=["user-read-private", "user-read-email", "user-read-recently-played"]
        )
        
        return True, spotify_profile, None
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return False, None, str(e)

async def refresh_spotify_token(client_id: str, client_secret: str, refresh_token: str) -> tuple[bool, Optional[SpotifyTokens], Optional[str]]:
    """Refresh Spotify access token"""
    try:
        auth_url = "https://accounts.spotify.com/api/token"
        
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
        
        response = requests.post(auth_url, headers=headers, data=data, timeout=10)
        
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

async def verify_spotify_credentials(client_id: str, client_secret: str) -> tuple[bool, Optional[SpotifyFullProfile], Optional[str]]:
    """Verify Spotify credentials and fetch user profile"""
    try:
        # Step 1: Get access token using Client Credentials flow
        auth_url = "https://accounts.spotify.com/api/token"
        
        # Encode credentials for basic auth
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials"
        }
        
        # Get access token
        response = requests.post(auth_url, headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to get Spotify access token: {response.status_code} - {response.text}")
            return False, None, f"Invalid Spotify credentials: {response.status_code}"
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            return False, None, "No access token received from Spotify"
        
        # Step 2: Try to get user profile (this requires user authorization, so we'll just verify the token works)
        # For now, we'll just verify that the credentials are valid by testing a simple API call
        test_url = "https://api.spotify.com/v1/search"
        test_headers = {
            "Authorization": f"Bearer {access_token}"
        }
        test_params = {
            "q": "test",
            "type": "track",
            "limit": 1
        }
        
        test_response = requests.get(test_url, headers=test_headers, params=test_params, timeout=10)
        
        if test_response.status_code == 200:
            # Credentials are valid - create a basic verified profile
            spotify_profile = SpotifyFullProfile(
                spotify_id=client_id,  # Using client_id as identifier for now
                display_name="Spotify Developer Account",
                verified=True,
                subscription_type="Developer"
            )
            return True, spotify_profile, None
        else:
            logger.error(f"Spotify API test failed: {test_response.status_code}")
            return False, None, "Spotify credentials appear invalid"
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error verifying Spotify credentials: {e}")
        return False, None, f"Network error: {str(e)}"
    except Exception as e:
        logger.error(f"Error verifying Spotify credentials: {e}")
        return False, None, f"Verification error: {str(e)}"

@app.post("/spotify/verify")
async def verify_spotify_account(request: SpotifyVerificationRequest):
    """Verify Spotify account credentials and fetch user profile"""
    try:
        logger.info(f"Starting Spotify verification for user: {request.user_id}")
        
        # Get user credentials from database
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_client_id, spotify_client_secret
            FROM users WHERE user_id = ?
        ''', (request.user_id,))
        
        user_data = cursor.fetchone()
        conn.close()
        
        if not user_data:
            logger.error(f"User not found in database: {request.user_id}")
            raise HTTPException(status_code=404, detail="User not found")
        
        client_id, encrypted_client_secret = user_data
        logger.info(f"Found user credentials for: {request.user_id}")
        
        # Decrypt the secret using secure vault
        try:
            client_secret = secure_decrypt_credential(request.user_id, encrypted_client_secret)
            logger.info("Successfully decrypted client secret from secure vault")
        except Exception as decrypt_error:
            logger.error(f"Failed to decrypt credentials from vault: {decrypt_error}")
            raise HTTPException(status_code=500, detail="Failed to decrypt credentials")
        
        # Verify with Spotify
        logger.info("Attempting Spotify API verification...")
        is_valid, spotify_profile, error_message = await verify_spotify_credentials(client_id, client_secret)
        
        if is_valid and spotify_profile:
            # Store verification status
            conn = sqlite3.connect('data/user_credentials.db')
            cursor = conn.cursor()
            
            # Update user with verification status
            cursor.execute('''
                UPDATE users 
                SET spotify_verified = ?, spotify_profile_data = ?, last_verification = ?
                WHERE user_id = ?
            ''', (True, json.dumps(spotify_profile.dict()), datetime.now().isoformat(), request.user_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Spotify verification successful for user: {request.user_id}")
            return {
                "verified": True,
                "spotify_profile": spotify_profile,
                "message": "Spotify account verified successfully"
            }
        else:
            logger.warning(f"Spotify verification failed for user {request.user_id}: {error_message}")
            return {
                "verified": False,
                "spotify_profile": None,
                "error": error_message or "Unknown verification error"
            }
            
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Spotify verification: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@app.get("/spotify/profile/{user_id}")
async def get_spotify_profile(user_id: str):
    """Get stored Spotify profile for a user"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_verified, spotify_profile_data, last_verification
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        is_verified, profile_data, last_verification = result
        
        if is_verified and profile_data:
            spotify_profile = json.loads(profile_data)
            return {
                "verified": True,
                "spotify_profile": spotify_profile,
                "last_verification": last_verification
            }
        else:
            return {
                "verified": False,
                "spotify_profile": None,
                "last_verification": None
            }
            
    except Exception as e:
        logger.error(f"Error fetching Spotify profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch profile: {str(e)}")

@app.post("/spotify/oauth/start")
async def start_spotify_oauth(request: SpotifyOAuthRequest):
    """Start Spotify OAuth flow for real user verification"""
    try:
        logger.info(f"Starting Spotify OAuth for user: {request.user_id}")
        
        # Get user credentials
        conn = sqlite3.connect('data/user_credentials.db')
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

@app.post("/spotify/oauth/callback")
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
        conn = sqlite3.connect('data/user_credentials.db')
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
        conn = sqlite3.connect('data/user_credentials.db')
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

@app.get("/spotify/profile/{user_id}/detailed")
async def get_detailed_spotify_profile(user_id: str):
    """Get comprehensive Spotify profile with real-time data"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_verified, spotify_profile_data, last_verification,
                   spotify_access_token, spotify_refresh_token, spotify_token_expires_at,
                   spotify_client_id, spotify_client_secret
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="User not found")
        
        (is_verified, profile_data, last_verification, 
         access_token, refresh_token, expires_at, client_id, encrypted_secret) = result
        
        if not is_verified or not profile_data:
            return {
                "verified": False,
                "spotify_profile": None,
                "last_verification": None,
                "connection_status": "not_verified"
            }
        
        # Check if token is expired and refresh if needed
        current_time = datetime.now()
        if expires_at:
            token_expires = datetime.fromisoformat(expires_at)
            if current_time >= token_expires and refresh_token:
                # Token expired, try to refresh
                logger.info(f"Refreshing expired token for user {user_id}")
                
                client_secret = secure_decrypt_credential(user_id, encrypted_secret)
                refresh_success, new_tokens, refresh_error = await refresh_spotify_token(
                    client_id, client_secret, refresh_token
                )
                
                if refresh_success and new_tokens:
                    # Update tokens in database
                    conn = sqlite3.connect('data/user_credentials.db')
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        UPDATE users 
                        SET spotify_access_token = ?, 
                            spotify_refresh_token = ?,
                            spotify_token_expires_at = ?
                        WHERE user_id = ?
                    ''', (new_tokens.access_token, new_tokens.refresh_token, 
                          new_tokens.expires_at, user_id))
                    
                    conn.commit()
                    conn.close()
                    
                    access_token = new_tokens.access_token
                    logger.info(f"Token refreshed successfully for user {user_id}")
                else:
                    logger.warning(f"Token refresh failed for user {user_id}: {refresh_error}")
                    # Return stored profile with expired status
                    stored_profile = json.loads(profile_data)
                    stored_profile["connection_status"] = "expired"
                    return {
                        "verified": True,
                        "spotify_profile": stored_profile,
                        "last_verification": last_verification,
                        "connection_status": "token_expired"
                    }
        
        # Get fresh profile data with current token
        if access_token:
            profile_success, fresh_profile, profile_error = await get_spotify_user_profile(access_token)
            
            if profile_success and fresh_profile:
                # Update stored profile with fresh data
                conn = sqlite3.connect('data/user_credentials.db')
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE users 
                    SET spotify_profile_data = ?, last_verification = ?
                    WHERE user_id = ?
                ''', (json.dumps(fresh_profile.dict()), datetime.now().isoformat(), user_id))
                
                conn.commit()
                conn.close()
                
                return {
                    "verified": True,
                    "spotify_profile": fresh_profile,
                    "last_verification": datetime.now().isoformat(),
                    "connection_status": "active"
                }
            else:
                logger.warning(f"Failed to get fresh profile for user {user_id}: {profile_error}")
        
        # Return stored profile if fresh fetch failed
        stored_profile = json.loads(profile_data)
        return {
            "verified": True,
            "spotify_profile": stored_profile,
            "last_verification": last_verification,
            "connection_status": "active" if access_token else "stored_data_only"
        }
        
    except Exception as e:
        logger.error(f"Error fetching detailed profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch detailed profile: {str(e)}")

@app.get("/spotify/profile/{user_id}/recently-played")
async def get_recently_played_tracks(user_id: str):
    """Get user's recently played tracks"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_access_token, spotify_verified
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[1]:  # Not verified
            raise HTTPException(status_code=404, detail="User not verified with Spotify")
        
        access_token = result[0]
        if not access_token:
            raise HTTPException(status_code=400, detail="No valid access token")
        
        # Get recently played tracks
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            "https://api.spotify.com/v1/me/player/recently-played?limit=20",
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch recently played tracks")
        
        data = response.json()
        recently_played = []
        
        for item in data.get("items", []):
            track = item["track"]
            recently_played.append({
                "track_name": track["name"],
                "artist_name": ", ".join([artist["name"] for artist in track["artists"]]),
                "album_name": track["album"]["name"],
                "played_at": item["played_at"],
                "track_uri": track["uri"],
                "external_url": track["external_urls"]["spotify"],
                "preview_url": track.get("preview_url"),
                "duration_ms": track.get("duration_ms"),
                "popularity": track.get("popularity")
            })
        
        return {
            "success": True,
            "recently_played": recently_played,
            "total_tracks": len(recently_played)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching recently played tracks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch recently played tracks: {str(e)}")

@app.post("/spotify/profile/{user_id}/refresh-connection")
async def refresh_spotify_connection(user_id: str):
    """Force refresh Spotify connection and profile data"""
    try:
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT spotify_access_token, spotify_refresh_token, spotify_client_id, 
                   spotify_client_secret, spotify_verified
            FROM users WHERE user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or not result[4]:  # Not verified
            raise HTTPException(status_code=404, detail="User not verified with Spotify")
        
        access_token, refresh_token, client_id, encrypted_secret, _ = result
        
        if not refresh_token:
            raise HTTPException(status_code=400, detail="No refresh token available")
        
        # Refresh the token
        client_secret = secure_decrypt_credential(user_id, encrypted_secret)
        refresh_success, new_tokens, refresh_error = await refresh_spotify_token(
            client_id, client_secret, refresh_token
        )
        
        if not refresh_success or not new_tokens:
            raise HTTPException(status_code=400, detail=f"Token refresh failed: {refresh_error}")
        
        # Get fresh profile
        profile_success, fresh_profile, profile_error = await get_spotify_user_profile(new_tokens.access_token)
        
        if not profile_success or not fresh_profile:
            raise HTTPException(status_code=400, detail=f"Profile refresh failed: {profile_error}")
        
        # Update database
        conn = sqlite3.connect('data/user_credentials.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET spotify_access_token = ?, 
                spotify_refresh_token = ?,
                spotify_token_expires_at = ?,
                spotify_profile_data = ?,
                last_verification = ?
            WHERE user_id = ?
        ''', (
            new_tokens.access_token, 
            new_tokens.refresh_token,
            new_tokens.expires_at,
            json.dumps(fresh_profile.dict()),
            datetime.now().isoformat(),
            user_id
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Connection refreshed successfully for user {user_id}")
        return {
            "success": True,
            "verified": True,
            "spotify_profile": fresh_profile,
            "message": "Connection refreshed successfully",
            "last_verification": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing connection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to refresh connection: {str(e)}")

# Enhanced Playlist Management Models for Phase C.3
class PlaylistSource(str, Enum):
    ANGHAMI = "anghami"
    SPOTIFY = "spotify"

class PlaylistType(str, Enum):
    OWNED = "owned"
    CREATED = "created" 
    FOLLOWED = "followed"
    ALL = "all"

class EnhancedPlaylist(BaseModel):
    id: str
    name: str
    source: PlaylistSource  # "anghami" or "spotify"
    type: PlaylistType  # "created", "followed", "owned"
    creator_name: Optional[str] = None
    owner_name: Optional[str] = None
    track_count: int = 0
    duration: Optional[str] = None
    duration_ms: Optional[int] = None
    description: Optional[str] = None
    cover_art_url: Optional[str] = None
    cover_art_local_path: Optional[str] = None
    external_url: Optional[str] = None
    is_public: Optional[bool] = None
    is_collaborative: Optional[bool] = None
    follower_count: Optional[int] = None
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    # Visual indicators
    type_indicator: str = ""  # 🎵 for owned/created, ➕ for followed
    source_indicator: str = ""  # Anghami/Spotify logos

class EnhancedPlaylistResponse(BaseModel):
    playlists: List[EnhancedPlaylist]
    pagination: Dict[str, Any]
    summary: Dict[str, Any]
    filters_applied: Dict[str, Any]

class PlaylistFilterRequest(BaseModel):
    sources: Optional[List[PlaylistSource]] = None  # ["anghami", "spotify"]
    types: Optional[List[PlaylistType]] = None  # ["created", "followed", "owned"]
    search_query: Optional[str] = None
    creator_filter: Optional[str] = None
    page: int = 1
    limit: int = 20
    sort_by: str = "name"  # name, track_count, created_at, last_modified
    sort_order: str = "asc"  # asc, desc
    user_id: Optional[str] = None  # Spotify user ID
    anghami_profile_url: Optional[str] = None  # Anghami profile URL

# Helper functions for internal use
async def get_anghami_playlists_internal(profile_url: str, type: str = "all", page: int = 1, limit: int = 20):
    """Internal function to get Anghami playlists"""
    return await get_anghami_playlists(profile_url=profile_url, type=type, page=page, limit=limit)

async def get_spotify_playlists_internal(user_id: str, type: str = "all", include_tracks: bool = False, page: int = 1, limit: int = 20):
    """Internal function to get Spotify playlists"""
    return await get_spotify_playlists(user_id=user_id, type=type, include_tracks=include_tracks, page=page, limit=limit)

async def get_anghami_playlists_summary_internal(profile_url: str):
    """Internal function to get Anghami playlists summary"""
    return await get_anghami_playlists_summary(profile_url=profile_url)

# Enhanced playlist endpoints for Phase C.3

@app.post("/playlists/enhanced")
async def get_enhanced_playlists(filters: PlaylistFilterRequest):
    """
    Enhanced playlist endpoint that provides both Anghami and Spotify playlists
    with filtering, search, and enhanced metadata for Phase C.3
    """
    try:
        logger.info(f"🎵 Getting enhanced playlists with filters: {filters.dict()}")
        
        all_playlists = []
        anghami_count = 0
        spotify_count = 0
        
        # Get Anghami playlists if requested
        if not filters.sources or PlaylistSource.ANGHAMI in filters.sources:
            try:
                # Use current profile if no URL provided
                profile_url = filters.anghami_profile_url or (current_profile.profile_url if current_profile else None)
                
                if profile_url:
                    # Always get all Anghami playlists, then filter on our side
                    anghami_playlists = await get_anghami_playlists_internal(
                        profile_url=profile_url,
                        type="all",  # Always get all types from Anghami
                        page=1,
                        limit=100  # Get all for client-side filtering
                    )
                    
                    # Convert to enhanced format
                    for playlist in anghami_playlists["playlists"]:
                        enhanced = EnhancedPlaylist(
                            id=playlist["id"],
                            name=playlist["name"],
                            source=PlaylistSource.ANGHAMI,
                            type=PlaylistType.CREATED if playlist["type"] == "created" else PlaylistType.FOLLOWED,
                            creator_name=playlist.get("creator_name"),
                            track_count=playlist.get("track_count", 0),
                            description=playlist.get("description"),
                            cover_art_url=playlist.get("cover_art_url"),
                            external_url=playlist.get("anghami_url"),
                            type_indicator="🎵" if playlist["type"] == "created" else "➕",
                            source_indicator="🎼"  # Anghami indicator
                        )
                        all_playlists.append(enhanced)
                        anghami_count += 1
                        
            except Exception as e:
                logger.warning(f"Could not load Anghami playlists: {e}")
        
        # Get Spotify playlists if requested
        if not filters.sources or PlaylistSource.SPOTIFY in filters.sources:
            if filters.user_id:
                # Always get all Spotify playlists, then filter on our side
                spotify_playlists = await get_spotify_playlists_internal(
                    user_id=filters.user_id,
                    type="all",  # Always get all types from Spotify
                    include_tracks=False,
                    page=1,
                    limit=100  # Get all for client-side filtering
                )
                
                # Convert to enhanced format
                for playlist in spotify_playlists["playlists"]:
                    playlist_type = PlaylistType.OWNED if playlist["type"] == "owned" else PlaylistType.FOLLOWED
                    
                    enhanced = EnhancedPlaylist(
                        id=playlist["id"],
                        name=playlist["name"],
                        source=PlaylistSource.SPOTIFY,
                        type=playlist_type,
                        owner_name=playlist.get("owner_name"),
                        track_count=playlist.get("track_count", 0),
                        duration=playlist.get("total_duration"),
                        description=playlist.get("description"),
                        cover_art_url=playlist.get("cover_art_url"),
                        external_url=playlist.get("external_url"),
                        is_public=playlist.get("is_public"),
                        is_collaborative=playlist.get("is_collaborative"),
                        follower_count=playlist.get("follower_count"),
                        type_indicator="🎵" if playlist["type"] == "owned" else "➕",
                        source_indicator="🎵"  # Spotify indicator
                    )
                    all_playlists.append(enhanced)
                    spotify_count += 1
            # No user_id provided - skip Spotify playlists
        
        # Apply search filter
        if filters.search_query:
            search_lower = filters.search_query.lower()
            all_playlists = [
                p for p in all_playlists
                if search_lower in p.name.lower() 
                or (p.description and search_lower in p.description.lower())
                or (p.creator_name and search_lower in p.creator_name.lower())
                or (p.owner_name and search_lower in p.owner_name.lower())
            ]
        
        # Apply type filter
        if filters.types:
            # Convert filter types to enum values if they're strings
            filter_types = []
            for filter_type in filters.types:
                if isinstance(filter_type, str):
                    if filter_type == "owned":
                        filter_types.append(PlaylistType.OWNED)
                    elif filter_type == "created":
                        filter_types.append(PlaylistType.CREATED)
                    elif filter_type == "followed":
                        filter_types.append(PlaylistType.FOLLOWED)
                else:
                    filter_types.append(filter_type)
            
            all_playlists = [p for p in all_playlists if p.type in filter_types]
        
        # Apply creator filter
        if filters.creator_filter:
            creator_lower = filters.creator_filter.lower()
            all_playlists = [
                p for p in all_playlists
                if (p.creator_name and creator_lower in p.creator_name.lower())
                or (p.owner_name and creator_lower in p.owner_name.lower())
            ]
        
        # Sort playlists
        reverse_order = filters.sort_order == "desc"
        if filters.sort_by == "name":
            all_playlists.sort(key=lambda p: p.name.lower(), reverse=reverse_order)
        elif filters.sort_by == "track_count":
            all_playlists.sort(key=lambda p: p.track_count, reverse=reverse_order)
        elif filters.sort_by == "created_at":
            all_playlists.sort(key=lambda p: p.created_at or "", reverse=reverse_order)
        elif filters.sort_by == "last_modified":
            all_playlists.sort(key=lambda p: p.last_modified or "", reverse=reverse_order)
        
        # Apply pagination
        total_playlists = len(all_playlists)
        start_idx = (filters.page - 1) * filters.limit
        end_idx = start_idx + filters.limit
        paginated_playlists = all_playlists[start_idx:end_idx]
        
        # Calculate pagination info
        total_pages = (total_playlists + filters.limit - 1) // filters.limit
        has_next = filters.page < total_pages
        has_prev = filters.page > 1
        
        # Create response
        response = EnhancedPlaylistResponse(
            playlists=paginated_playlists,
            pagination={
                "page": filters.page,
                "limit": filters.limit,
                "total": total_playlists,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev
            },
            summary={
                "total_anghami": anghami_count,
                "total_spotify": spotify_count,
                "total_all": total_playlists,
                "displayed": len(paginated_playlists),
                "anghami_created": len([p for p in all_playlists if p.source == PlaylistSource.ANGHAMI and p.type == PlaylistType.CREATED]),
                "anghami_followed": len([p for p in all_playlists if p.source == PlaylistSource.ANGHAMI and p.type == PlaylistType.FOLLOWED]),
                "spotify_owned": len([p for p in all_playlists if p.source == PlaylistSource.SPOTIFY and p.type == PlaylistType.OWNED]),
                "spotify_followed": len([p for p in all_playlists if p.source == PlaylistSource.SPOTIFY and p.type == PlaylistType.FOLLOWED])
            },
            filters_applied={
                "sources": filters.sources or ["anghami", "spotify"],
                "types": filters.types or ["all"],
                "search_query": filters.search_query,
                "creator_filter": filters.creator_filter,
                "sort_by": filters.sort_by,
                "sort_order": filters.sort_order
            }
        )
        
        logger.info(f"✅ Enhanced playlists response: {total_playlists} total, {len(paginated_playlists)} displayed")
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced playlists endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/enhanced/sources")
async def get_available_playlist_sources(user_id: str = None, anghami_profile_url: str = None):
    """Get available playlist sources and their counts"""
    try:
        sources = {}
        
        # Check Anghami availability
        if anghami_profile_url or (current_profile and current_profile.is_valid):
            try:
                profile_url = anghami_profile_url or current_profile.profile_url
                anghami_summary = await get_anghami_playlists_summary_internal(profile_url)
                sources["anghami"] = {
                    "available": True,
                    "total_created": anghami_summary.get("total_created", 0),
                    "total_followed": anghami_summary.get("total_followed", 0),
                    "total_all": anghami_summary.get("total_all", 0),
                    "profile_name": anghami_summary.get("profile_name")
                }
            except Exception as e:
                sources["anghami"] = {"available": False, "error": str(e)}
        else:
            sources["anghami"] = {"available": False, "error": "No Anghami profile selected"}
        
        # Check Spotify availability
        if user_id:
            try:
                spotify_summary = await get_spotify_playlists_internal(user_id, type="all", page=1, limit=1)
                sources["spotify"] = {
                    "available": True,
                    "total_owned": spotify_summary["summary"]["total_owned"],
                    "total_followed": spotify_summary["summary"]["total_followed"],
                    "total_all": spotify_summary["summary"]["total_all"],
                    "user_name": spotify_summary["summary"]["user_display_name"]
                }
            except Exception as e:
                sources["spotify"] = {"available": False, "error": str(e)}
        else:
            sources["spotify"] = {"available": False, "error": "No Spotify user authenticated"}
        
        return sources
        
    except Exception as e:
        logger.error(f"❌ Error getting available sources: {e}")
        return {"anghami": {"available": False}, "spotify": {"available": False}}

# Main entry point
if __name__ == "__main__":
    print("🎵 Starting Anghami → Spotify Migration API Server...")
    print("📡 API will be available at: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔗 Frontend should connect to: http://localhost:8000")
    print("")
    
    uvicorn.run(
        "backend_api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    ) 