#!/usr/bin/env python3
"""
Anghami Data Models

Data structures for representing Anghami playlists, tracks, and related metadata.
These models are used throughout the migration process for data consistency.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class AnghamiTrack:
    """Represents a single track from Anghami with available metadata"""
    
    title: str
    artists: List[str]
    
    def __post_init__(self):
        """Validate and clean track data after initialization"""
        # Clean title and artist names
        self.title = self.title.strip() if self.title else ""
        self.artists = [artist.strip() for artist in self.artists if artist and artist.strip()]
    
    @property
    def primary_artist(self) -> str:
        """Get the primary (first) artist"""
        return self.artists[0] if self.artists else ""
    
    @property
    def all_artists_string(self) -> str:
        """Get all artists as a comma-separated string"""
        return ", ".join(self.artists)
    
    def to_search_query(self) -> str:
        """Generate a search query string for Spotify API"""
        query_parts = []
        
        if self.title:
            query_parts.append(f'track:"{self.title}"')
        
        if self.primary_artist:
            query_parts.append(f'artist:"{self.primary_artist}"')
        
        return " ".join(query_parts)
    
    def to_simple_search_query(self) -> str:
        """Generate a simple search query without field specifications"""
        if self.title and self.primary_artist:
            return f"{self.title} {self.primary_artist}"
        elif self.title:
            return self.title
        else:
            return self.primary_artist


@dataclass_json
@dataclass
class AnghamiPlaylist:
    """Represents an Anghami playlist with metadata and tracks"""
    
    id: str
    name: str
    url: str
    description: Optional[str] = None
    cover_art_url: Optional[str] = None
    track_count: int = 0
    is_public: bool = True
    created_date: Optional[datetime] = None
    tracks: List[AnghamiTrack] = field(default_factory=list)
    creator_name: Optional[str] = None
    
    def __post_init__(self):
        """Validate and clean playlist data after initialization"""
        # Clean playlist name
        self.name = self.name.strip() if self.name else "Untitled Playlist"
        
        # Clean description
        if self.description:
            self.description = self.description.strip()
            if not self.description:
                self.description = None
        
        # Update track count from actual tracks if available
        if self.tracks:
            self.track_count = len(self.tracks)
    
    @property
    def total_duration_seconds(self) -> int:
        """Calculate total duration of all tracks in seconds - Not available from Anghami extraction"""
        return 0  # Duration not extracted from Anghami
    
    @property
    def total_duration_formatted(self) -> str:
        """Get total duration in HH:MM:SS format - Not available from Anghami extraction"""
        return "Unknown"  # Duration not extracted from Anghami
    
    @property
    def has_cover_art(self) -> bool:
        """Check if playlist has cover art URL"""
        return bool(self.cover_art_url and self.cover_art_url.strip())
    
    def add_track(self, track: AnghamiTrack) -> None:
        """Add a track to the playlist"""
        self.tracks.append(track)
        self.track_count = len(self.tracks)
    
    def get_tracks_by_artist(self, artist_name: str) -> List[AnghamiTrack]:
        """Get all tracks by a specific artist"""
        artist_name_lower = artist_name.lower()
        return [
            track for track in self.tracks
            if any(artist_name_lower in artist.lower() for artist in track.artists)
        ]
    
    def get_missing_metadata_tracks(self) -> List[AnghamiTrack]:
        """Get tracks that are missing essential metadata"""
        return [
            track for track in self.tracks
            if not track.title or not track.artists
        ]


@dataclass_json
@dataclass
class AnghamiProfile:
    """Represents an Anghami user profile with their playlists"""
    
    username: str
    profile_url: str
    display_name: Optional[str] = None
    follower_count: int = 0
    following_count: int = 0
    playlists: List[AnghamiPlaylist] = field(default_factory=list)
    profile_image_url: Optional[str] = None
    
    def __post_init__(self):
        """Validate and clean profile data after initialization"""
        self.username = self.username.strip() if self.username else ""
        
        if self.display_name:
            self.display_name = self.display_name.strip()
            if not self.display_name:
                self.display_name = None
    
    @property
    def total_playlists(self) -> int:
        """Get total number of playlists"""
        return len(self.playlists)
    
    @property
    def total_tracks(self) -> int:
        """Get total number of tracks across all playlists"""
        return sum(playlist.track_count for playlist in self.playlists)
    
    def get_public_playlists(self) -> List[AnghamiPlaylist]:
        """Get only public playlists"""
        return [playlist for playlist in self.playlists if playlist.is_public]
    
    def get_playlists_with_tracks(self) -> List[AnghamiPlaylist]:
        """Get playlists that have tracks loaded"""
        return [playlist for playlist in self.playlists if playlist.tracks]
    
    def add_playlist(self, playlist: AnghamiPlaylist) -> None:
        """Add a playlist to the profile"""
        self.playlists.append(playlist)


@dataclass_json
@dataclass
class ScrapingResult:
    """Represents the result of a scraping operation"""
    
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def success_result(cls, data: Any, response_time_ms: int = 0) -> 'ScrapingResult':
        """Create a successful scraping result"""
        return cls(
            success=True,
            data=data,
            response_time_ms=response_time_ms
        )
    
    @classmethod
    def error_result(cls, error_message: str, status_code: Optional[int] = None) -> 'ScrapingResult':
        """Create a failed scraping result"""
        return cls(
            success=False,
            error_message=error_message,
            status_code=status_code
        )


@dataclass_json
@dataclass
class MigrationStats:
    """Statistics for tracking migration progress"""
    
    playlists_total: int = 0
    playlists_completed: int = 0
    playlists_failed: int = 0
    tracks_total: int = 0
    tracks_migrated: int = 0
    tracks_missing: int = 0
    tracks_failed: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def playlists_success_rate(self) -> float:
        """Calculate playlist migration success rate"""
        if self.playlists_total == 0:
            return 0.0
        return (self.playlists_completed / self.playlists_total) * 100
    
    @property
    def tracks_success_rate(self) -> float:
        """Calculate track migration success rate"""
        if self.tracks_total == 0:
            return 0.0
        return (self.tracks_migrated / self.tracks_total) * 100
    
    @property
    def duration_seconds(self) -> int:
        """Calculate migration duration in seconds"""
        if not self.start_time or not self.end_time:
            return 0
        return int((self.end_time - self.start_time).total_seconds())
    
    def update_playlist_completed(self, tracks_migrated: int, tracks_missing: int) -> None:
        """Update stats when a playlist is completed"""
        self.playlists_completed += 1
        self.tracks_migrated += tracks_migrated
        self.tracks_missing += tracks_missing
    
    def update_playlist_failed(self) -> None:
        """Update stats when a playlist fails"""
        self.playlists_failed += 1 