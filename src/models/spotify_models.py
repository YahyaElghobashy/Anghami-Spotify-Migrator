#!/usr/bin/env python3
"""
Spotify Data Models
Similar structure to anghami_models.py for consistency
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

@dataclass
class SpotifyTrack:
    """Represents a track in a Spotify playlist"""
    id: str
    title: str
    artists: List[str] = field(default_factory=list)
    album: Optional[str] = None
    duration_ms: Optional[int] = None
    preview_url: Optional[str] = None
    external_url: Optional[str] = None
    track_number: Optional[int] = None
    explicit: bool = False
    popularity: Optional[int] = None
    added_at: Optional[str] = None  # When added to playlist
    added_by: Optional[str] = None  # User who added it
    
    @property
    def primary_artist(self) -> str:
        """Get the primary artist name"""
        return self.artists[0] if self.artists else "Unknown Artist"
    
    @property
    def duration_formatted(self) -> str:
        """Get duration in MM:SS format"""
        if not self.duration_ms:
            return "Unknown"
        
        seconds = self.duration_ms // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:02d}"

@dataclass
class SpotifyPlaylist:
    """Represents a Spotify playlist"""
    id: str
    name: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    owner_name: Optional[str] = None
    is_owned: bool = False  # True if current user owns it
    is_followed: bool = False  # True if current user follows it
    is_public: bool = True
    is_collaborative: bool = False
    track_count: int = 0
    follower_count: Optional[int] = None
    cover_art_url: Optional[str] = None
    cover_art_local_path: Optional[str] = None
    external_url: Optional[str] = None
    tracks: List[SpotifyTrack] = field(default_factory=list)
    created_at: Optional[str] = None
    last_modified: Optional[str] = None
    
    @property
    def total_duration_ms(self) -> int:
        """Calculate total duration of all tracks"""
        return sum(track.duration_ms or 0 for track in self.tracks)
    
    @property
    def total_duration_formatted(self) -> str:
        """Get total duration in human readable format"""
        total_seconds = self.total_duration_ms // 1000
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert playlist to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "is_owned": self.is_owned,
            "is_followed": self.is_followed,
            "is_public": self.is_public,
            "is_collaborative": self.is_collaborative,
            "track_count": self.track_count,
            "follower_count": self.follower_count,
            "cover_art_url": self.cover_art_url,
            "cover_art_local_path": self.cover_art_local_path,
            "external_url": self.external_url,
            "total_duration_ms": self.total_duration_ms,
            "total_duration_formatted": self.total_duration_formatted,
            "created_at": self.created_at,
            "last_modified": self.last_modified,
            "tracks": [
                {
                    "id": track.id,
                    "title": track.title,
                    "artists": track.artists,
                    "album": track.album,
                    "duration_ms": track.duration_ms,
                    "duration_formatted": track.duration_formatted,
                    "preview_url": track.preview_url,
                    "external_url": track.external_url,
                    "track_number": track.track_number,
                    "explicit": track.explicit,
                    "popularity": track.popularity,
                    "added_at": track.added_at,
                    "added_by": track.added_by
                }
                for track in self.tracks
            ]
        }

@dataclass
class SpotifyUserPlaylists:
    """Container for user's Spotify playlists with type separation"""
    user_id: str
    display_name: Optional[str] = None
    owned_playlists: List[SpotifyPlaylist] = field(default_factory=list)
    followed_playlists: List[SpotifyPlaylist] = field(default_factory=list)
    total_owned: int = 0
    total_followed: int = 0
    extraction_timestamp: Optional[str] = None
    
    def __post_init__(self):
        """Update counts after initialization"""
        self.total_owned = len(self.owned_playlists)
        self.total_followed = len(self.followed_playlists)
        if not self.extraction_timestamp:
            self.extraction_timestamp = datetime.now().isoformat()
    
    @property
    def all_playlists(self) -> List[SpotifyPlaylist]:
        """Get all playlists combined"""
        return self.owned_playlists + self.followed_playlists
    
    @property
    def total_playlists(self) -> int:
        """Get total number of playlists"""
        return self.total_owned + self.total_followed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "total_owned": self.total_owned,
            "total_followed": self.total_followed,
            "total_playlists": self.total_playlists,
            "extraction_timestamp": self.extraction_timestamp,
            "owned_playlists": [playlist.to_dict() for playlist in self.owned_playlists],
            "followed_playlists": [playlist.to_dict() for playlist in self.followed_playlists]
        } 