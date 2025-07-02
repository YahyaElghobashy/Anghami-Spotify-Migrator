"""
Module: Migration Models
Purpose: Pydantic models for playlist migration process and status tracking
Contains: MigrationRequest, MigrationStatus, AuthStatus
"""

from typing import Optional, List, Dict
from pydantic import BaseModel

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