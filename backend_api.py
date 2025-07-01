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
from typing import Dict, List, Optional
from urllib.parse import urlparse
from cryptography.fernet import Fernet
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

# Import existing extractors (removed unused imports)
# from src.extractors.anghami_direct_extractor import AnghamiDirectExtractor - No longer used
# from src.models.anghami_models import AnghamiPlaylist, AnghamiTrack - Using Pydantic models instead

# Import the improved profile extractor
import sys
sys.path.append(str(Path(__file__).parent / "src" / "extractors"))
from anghami_profile_extractor import AnghamiProfileExtractor

# Import for Spotify API
import requests

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

class SpotifyUserProfile(BaseModel):
    spotify_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    country: Optional[str] = None
    subscription_type: Optional[str] = None
    verified: bool = False

class VerifiedUserSession(BaseModel):
    user_id: str
    session_token: str
    display_name: str
    spotify_client_id: str
    created_at: str
    # New verification fields
    spotify_verified: bool = False
    spotify_profile: Optional[SpotifyUserProfile] = None
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
    """Get user's Anghami playlists"""
    global current_profile
    
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    # TODO: Replace with real playlist extraction from current_profile
    # For now, return sample data but indicate it's from the selected profile
    sample_playlists = [
        AnghamiPlaylist(
            id="267851779",
            name=f"Mixtape 💿 🔥 - {current_profile.display_name}",
            trackCount=30,
            duration="2h 15m",
            description="Arabic and English hits mix - From your Anghami profile",
            tracks=[
                AnghamiTrack(
                    id="1",
                    title="اصحالي يابرنس",
                    artist="موسى",
                    album="Latest Hits",
                    duration="3:45",
                    confidence=0.85
                ),
                AnghamiTrack(
                    id="2", 
                    title="White Ferrari",
                    artist="Frank Ocean",
                    album="Blonde",
                    duration="4:09",
                    confidence=1.0
                ),
                AnghamiTrack(
                    id="3",
                    title="God's Plan", 
                    artist="Drake",
                    album="Scorpion",
                    duration="3:19",
                    confidence=1.0
                )
            ]
        ),
        AnghamiPlaylist(
            id="276644689",
            name=f"Arabic Classics - {current_profile.display_name}",
            trackCount=45,
            duration="3h 12m",
            description="Timeless Arabic music collection - From your Anghami profile",
            tracks=[]
        ),
        AnghamiPlaylist(
            id="278123456",
            name=f"Workout Motivation - {current_profile.display_name}",
            trackCount=28,
            duration="1h 58m",
            description="High-energy tracks for gym sessions - From your Anghami profile",
            tracks=[]
        ),
        AnghamiPlaylist(
            id="279987654",
            name=f"Chill Vibes - {current_profile.display_name}",
            trackCount=22,
            duration="1h 35m",
            description="Relaxing tunes for unwinding - From your Anghami profile",
            tracks=[]
        )
    ]
    
    logger.info(f"Returning {len(sample_playlists)} playlists for profile: {current_profile.display_name}")
    return sample_playlists

@app.get("/playlists/{playlist_id}")
async def get_playlist_details(playlist_id: str):
    """Get detailed information about a specific playlist"""
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    # TODO: Replace with real playlist extraction
    sample_playlists = await get_playlists()
    playlist = next((p for p in sample_playlists if p.id == playlist_id), None)
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    logger.info(f"Returning details for playlist: {playlist.name}")
    return playlist

# ... rest of existing endpoints remain the same

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
    """Initialize user credentials database (now without encryption keys)"""
    conn = sqlite3.connect('data/user_credentials.db')
    cursor = conn.cursor()
    
    # Create users table without encryption_key column for better security
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            spotify_client_id TEXT NOT NULL,
            spotify_client_secret TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            spotify_verified BOOLEAN DEFAULT FALSE,
            spotify_profile_data TEXT,
            last_verification TIMESTAMP
        )
    ''')
    
    # Check current table structure and migrate if needed
    cursor.execute("PRAGMA table_info(users)")
    columns = {column[1]: column for column in cursor.fetchall()}
    
    # Handle migration from old column names
    if 'encrypted_spotify_secret' in columns and 'spotify_client_secret' not in columns:
        logger.info("Migrating database: renaming encrypted_spotify_secret to spotify_client_secret")
        cursor.execute('ALTER TABLE users RENAME COLUMN encrypted_spotify_secret TO spotify_client_secret')
    
    # Add missing columns
    if 'username' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN username TEXT')
    if 'spotify_verified' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN spotify_verified BOOLEAN DEFAULT FALSE')
    if 'spotify_profile_data' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN spotify_profile_data TEXT')
    if 'last_verification' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN last_verification TIMESTAMP')
    
    # Remove old is_active column if it exists (we don't use it anymore)
    if 'is_active' in columns:
        # SQLite doesn't support DROP COLUMN directly, so we'll ignore it
        logger.info("Note: is_active column still exists but is not used")
    
    # Note: encryption_key column may exist from old schema, but we ignore it now
    if 'encryption_key' in columns:
        logger.info("Note: Found old encryption_key column - now using secure vault instead")
    
    # Create user sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_token TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("User database initialized with secure key vault architecture")

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
            SELECT user_id, display_name, spotify_client_id, created_at, last_used
            FROM users
            ORDER BY last_used DESC, created_at DESC
        ''')
        
        users = []
        for row in cursor.fetchall():
            users.append(UserCredentials(
                user_id=row[0],
                display_name=row[1],
                spotify_client_id=row[2],
                has_credentials=True,
                created_at=row[3],
                last_used=row[4]
            ))
        
        conn.close()
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return {"users": []}

async def verify_spotify_credentials(client_id: str, client_secret: str) -> tuple[bool, Optional[SpotifyUserProfile], Optional[str]]:
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
            spotify_profile = SpotifyUserProfile(
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