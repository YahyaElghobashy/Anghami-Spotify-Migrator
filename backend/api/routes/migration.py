"""
Module: Migration Routes
Purpose: Playlist migration process endpoints
Contains: start_migration, get_migration_status, stop_migration, websocket_endpoint
"""

import asyncio
from fastapi import APIRouter, HTTPException, WebSocket
from ...core.logging import get_logger
from ...models.migration_models import MigrationRequest
from ...models.anghami_models import AnghamiPlaylist
from ...services.migration_service import (
    generate_session_id,
    create_migration_status,
    create_migration_session,
    get_migration_status as get_status,
    stop_migration as stop_migration_service,
    simulate_migration
)
from ...websocket.handlers import websocket_endpoint

logger = get_logger(__name__)
router = APIRouter(prefix="/migrate", tags=["migration"])

# Import current profile from profiles module
def get_current_profile():
    from .profiles import get_current_profile
    return get_current_profile()

@router.post("")
async def start_migration(request: MigrationRequest):
    """Start playlist migration"""
    current_profile = get_current_profile()
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    session_id = generate_session_id()
    
    # Create sample playlists for migration (in real implementation, get from service)
    sample_playlists = []
    for i, playlist_id in enumerate(request.playlist_ids):
        sample_playlists.append(AnghamiPlaylist(
            id=playlist_id,
            name=f"Sample Playlist {i+1}",
            trackCount=10 + (i * 5),
            duration=f"{10 + (i * 5)} tracks"
        ))
    
    total_tracks = sum(p.trackCount for p in sample_playlists)
    
    # Initialize migration status
    migration_status = create_migration_status(session_id, request.playlist_ids, total_tracks)
    migration_status.message = f"Starting playlist extraction from {current_profile.display_name}'s Anghami profile..."
    
    create_migration_session(session_id, migration_status)
    
    # Start background migration task
    asyncio.create_task(simulate_migration(session_id, request.playlist_ids))
    
    logger.info(f"Started migration session: {session_id} for profile: {current_profile.display_name}")
    return {"sessionId": session_id}

@router.get("/status/{session_id}")
async def get_migration_status(session_id: str):
    """Get migration status"""
    status = get_status(session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Migration session not found")
    
    return status

@router.post("/{session_id}/stop")
async def stop_migration(session_id: str):
    """Stop migration"""
    success = stop_migration_service(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Migration session not found")
    
    logger.info(f"Stopped migration session: {session_id}")
    return {"success": True}

@router.websocket("/ws/{session_id}")
async def websocket_migration_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time migration updates"""
    await websocket_endpoint(websocket, session_id) 