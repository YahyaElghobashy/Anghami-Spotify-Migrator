"""
Module: Spotify Models
Purpose: Pydantic models for Spotify authentication, profiles, and data
Contains: SpotifyVerificationRequest, SpotifyTokens, SpotifyOAuthRequest, SpotifyRecentlyPlayed, SpotifyFullProfile
"""

from typing import Optional, List
from pydantic import BaseModel

class SpotifyVerificationRequest(BaseModel):
    user_id: str

class SpotifyTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: str
    scope: str

class SpotifyOAuthRequest(BaseModel):
    user_id: str
    redirect_uri: str = "http://127.0.0.1:8888/callback"

class SpotifyRecentlyPlayed(BaseModel):
    track_name: str
    artist_name: str
    album_name: str
    played_at: str
    track_uri: str
    external_url: str

class SpotifyFullProfile(BaseModel):
    spotify_id: str
    display_name: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    country: Optional[str] = None
    subscription_type: Optional[str] = None
    verified: bool = False
    # Enhanced data
    total_public_playlists: Optional[int] = None
    total_following: Optional[int] = None
    recently_played: Optional[List[SpotifyRecentlyPlayed]] = None
    connection_status: str = "active"  # active, expired, invalid
    last_activity: Optional[str] = None
    oauth_scopes: Optional[List[str]] = None 