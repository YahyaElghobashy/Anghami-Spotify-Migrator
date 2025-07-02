"""
Module: Migration Service
Purpose: Business logic for playlist migration process and status tracking
Contains: simulate_migration, migration session management, global state management
"""

import asyncio
import uuid
from typing import Dict, List
from fastapi import WebSocket
from ..core.logging import get_logger
from ..models.migration_models import MigrationStatus, MigrationRequest

logger = get_logger(__name__)

# Global state storage (these will be managed by the service)
migration_sessions: Dict[str, MigrationStatus] = {}
websocket_connections: Dict[str, WebSocket] = {}

def get_migration_sessions() -> Dict[str, MigrationStatus]:
    """Get the migration sessions dictionary"""
    return migration_sessions

def get_websocket_connections() -> Dict[str, WebSocket]:
    """Get the websocket connections dictionary"""
    return websocket_connections

def create_migration_session(session_id: str, migration_status: MigrationStatus) -> None:
    """Create a new migration session"""
    migration_sessions[session_id] = migration_status
    logger.info(f"Created migration session: {session_id}")

def get_migration_status(session_id: str) -> MigrationStatus:
    """Get migration status for a session"""
    return migration_sessions.get(session_id)

def update_migration_status(session_id: str, **kwargs) -> None:
    """Update migration status fields"""
    if session_id in migration_sessions:
        for key, value in kwargs.items():
            setattr(migration_sessions[session_id], key, value)

def stop_migration(session_id: str) -> bool:
    """Stop migration for a session"""
    if session_id in migration_sessions:
        migration_sessions[session_id].status = "stopped"
        migration_sessions[session_id].message = "Migration stopped by user"
        logger.info(f"Stopped migration session: {session_id}")
        return True
    return False

def register_websocket(session_id: str, websocket: WebSocket) -> None:
    """Register a WebSocket connection for a session"""
    websocket_connections[session_id] = websocket
    logger.info(f"WebSocket connected for session: {session_id}")

def unregister_websocket(session_id: str) -> None:
    """Unregister a WebSocket connection"""
    if session_id in websocket_connections:
        del websocket_connections[session_id]
        logger.info(f"WebSocket disconnected for session: {session_id}")

async def simulate_migration(session_id: str, playlist_ids: List[str]):
    """Simulate the migration process with realistic progress updates"""
    if session_id not in migration_sessions:
        return
    
    status = migration_sessions[session_id]
    
    # For simulation purposes, create mock playlist data
    mock_playlists = []
    for i, playlist_id in enumerate(playlist_ids):
        mock_playlists.append({
            "id": playlist_id,
            "name": f"Playlist {i+1}",
            "trackCount": 10 + (i * 5)  # Vary track counts
        })
    
    try:
        # Phase 1: Extraction (0-25%)
        status.status = "extracting"
        status.message = "Extracting playlists from Anghami..."
        
        for i, playlist in enumerate(mock_playlists):
            status.progress = (i / len(mock_playlists)) * 25
            status.currentPlaylist = playlist["name"]
            status.message = f"Extracting: {playlist['name']}"
            await asyncio.sleep(2)  # Simulate extraction time
        
        # Phase 2: Matching (25-75%)
        status.status = "matching"
        status.message = "Matching tracks with Spotify..."
        
        total_tracks = sum(p["trackCount"] for p in mock_playlists)
        matched_count = 0
        
        for playlist in mock_playlists:
            status.currentPlaylist = playlist["name"]
            
            for track_num in range(playlist["trackCount"]):
                matched_count += 1
                status.matchedTracks = matched_count
                status.progress = 25 + (matched_count / total_tracks) * 50
                status.message = f"Matching tracks in: {playlist['name']} ({track_num + 1}/{playlist['trackCount']})"
                
                # Simulate some tracks that need review (Arabic tracks)
                if "Arabic" in playlist["name"] or "موسى" in playlist["name"]:
                    status.message += " - Reviewing Arabic track match"
                
                await asyncio.sleep(0.5)  # Simulate matching time
        
        # Phase 3: Creating (75-100%)
        status.status = "creating"
        status.message = "Creating playlists in Spotify..."
        
        for i, playlist in enumerate(mock_playlists):
            status.currentPlaylist = playlist["name"]
            status.progress = 75 + ((i + 1) / len(mock_playlists)) * 25
            status.message = f"Creating Spotify playlist: {playlist['name']}"
            status.completedPlaylists = i + 1
            status.createdPlaylists = i + 1
            await asyncio.sleep(3)  # Simulate playlist creation time
        
        # Complete
        status.status = "completed"
        status.progress = 100.0
        status.message = f"Successfully migrated {len(mock_playlists)} playlists!"
        status.currentPlaylist = None
        
        logger.info(f"Migration completed for session: {session_id}")
        
    except Exception as e:
        status.status = "error"
        status.errors.append(str(e))
        status.message = f"Migration failed: {str(e)}"
        logger.error(f"Migration failed for session {session_id}: {e}")

def generate_session_id() -> str:
    """Generate a unique session ID for migration"""
    return str(uuid.uuid4())

def create_migration_status(session_id: str, playlist_ids: List[str], total_tracks: int = 0) -> MigrationStatus:
    """Create initial migration status"""
    return MigrationStatus(
        sessionId=session_id,
        status="extracting",
        progress=0.0,
        totalPlaylists=len(playlist_ids),
        completedPlaylists=0,
        totalTracks=total_tracks,
        matchedTracks=0,
        createdPlaylists=0,
        errors=[],
        message="Starting playlist extraction..."
    ) 