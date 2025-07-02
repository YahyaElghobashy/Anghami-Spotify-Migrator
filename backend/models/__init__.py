"""
Models module for Anghami → Spotify Migration Backend
Contains all Pydantic models organized by functionality
"""

# User Models
from .user_models import (
    UserSetupRequest,
    UserCredentials,
    UserSession,
    VerifiedUserSession
)

# Anghami Models
from .anghami_models import (
    ProfileValidationRequest,
    ProfileData,
    ProfileHistoryItem,
    AnghamiTrack,
    AnghamiPlaylist
)

# Spotify Models
from .spotify_models import (
    SpotifyVerificationRequest,
    SpotifyTokens,
    SpotifyOAuthRequest,
    SpotifyRecentlyPlayed,
    SpotifyFullProfile
)

# Migration Models
from .migration_models import (
    MigrationRequest,
    MigrationStatus,
    AuthStatus
)

# Playlist Models
from .playlist_models import (
    PlaylistSource,
    PlaylistType,
    EnhancedPlaylist,
    EnhancedPlaylistResponse,
    PlaylistFilterRequest
)

__all__ = [
    # User Models
    "UserSetupRequest",
    "UserCredentials", 
    "UserSession",
    "VerifiedUserSession",
    # Anghami Models
    "ProfileValidationRequest",
    "ProfileData",
    "ProfileHistoryItem",
    "AnghamiTrack",
    "AnghamiPlaylist",
    # Spotify Models
    "SpotifyVerificationRequest",
    "SpotifyTokens",
    "SpotifyOAuthRequest",
    "SpotifyRecentlyPlayed",
    "SpotifyFullProfile",
    # Migration Models
    "MigrationRequest",
    "MigrationStatus",
    "AuthStatus",
    # Playlist Models
    "PlaylistSource",
    "PlaylistType",
    "EnhancedPlaylist",
    "EnhancedPlaylistResponse",
    "PlaylistFilterRequest"
]
