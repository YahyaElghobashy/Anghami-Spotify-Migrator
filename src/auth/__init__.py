"""
Authentication

Contains authentication handlers for Spotify and other services.
"""

from .spotify_auth import SpotifyAuth, create_spotify_auth

__all__ = ['SpotifyAuth', 'create_spotify_auth'] 