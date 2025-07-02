"""
Module: WebSocket Handlers
Purpose: WebSocket connection management for real-time migration updates
Contains: websocket_endpoint, connection management functions
"""

import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from ..core.logging import get_logger
from ..services.migration_service import (
    get_migration_sessions, 
    register_websocket, 
    unregister_websocket
)

logger = get_logger(__name__)

async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time migration updates"""
    await websocket.accept()
    register_websocket(session_id, websocket)
    
    logger.info(f"WebSocket connected for session: {session_id}")
    
    try:
        while True:
            # Send current status
            migration_sessions = get_migration_sessions()
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
        unregister_websocket(session_id)

async def handle_websocket_connection(websocket: WebSocket, session_id: str):
    """Handle a WebSocket connection for migration updates"""
    await websocket_endpoint(websocket, session_id) 