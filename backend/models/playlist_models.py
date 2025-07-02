"""
Module: Playlist Models
Purpose: Pydantic models for enhanced playlist management across sources
Contains: PlaylistSource, PlaylistType, EnhancedPlaylist, EnhancedPlaylistResponse, PlaylistFilterRequest
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel

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