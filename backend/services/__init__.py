"""
Services module for Anghami → Spotify Migration Backend
Contains business logic services for different domains
"""

# Anghami Service
from .anghami_service import (
    validate_anghami_profile_url,
    extract_profile_id,
    fetch_anghami_profile_data,
    get_anghami_playlists_internal,
    get_anghami_playlists_summary_internal
)

# Spotify Service  
from .spotify_service import (
    get_spotify_oauth_url,
    verify_spotify_credentials,
    exchange_spotify_code_for_tokens,
    get_spotify_user_profile,
    refresh_spotify_token,
    get_user_spotify_access_token,
    get_spotify_playlists_internal
)

# Migration Service
from .migration_service import (
    get_migration_sessions,
    get_websocket_connections,
    create_migration_session,
    get_migration_status,
    update_migration_status,
    stop_migration,
    register_websocket,
    unregister_websocket,
    simulate_migration,
    generate_session_id,
    create_migration_status
)

# Playlist Service
from .playlist_service import (
    get_available_playlist_sources,
)

__all__ = [
    # Anghami Service
    "validate_anghami_profile_url",
    "extract_profile_id", 
    "fetch_anghami_profile_data",
    "get_anghami_playlists_internal",
    "get_anghami_playlists_summary_internal",
    # Spotify Service
    "get_spotify_oauth_url",
    "verify_spotify_credentials",
    "exchange_spotify_code_for_tokens",
    "get_spotify_user_profile",
    "refresh_spotify_token",
    "get_user_spotify_access_token",
    "get_spotify_playlists_internal",
    # Migration Service
    "get_migration_sessions",
    "get_websocket_connections",
    "create_migration_session",
    "get_migration_status",
    "update_migration_status",
    "stop_migration",
    "register_websocket",
    "unregister_websocket",
    "simulate_migration",
    "generate_session_id",
    "create_migration_status",
    # Playlist Service
    "get_available_playlist_sources",
]
