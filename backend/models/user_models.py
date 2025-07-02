"""
Module: User Models
Purpose: Pydantic models for user management, authentication, and sessions
Contains: UserSetupRequest, UserCredentials, UserSession, VerifiedUserSession
"""

from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from .spotify_models import SpotifyFullProfile
    from .anghami_models import ProfileData

class UserSetupRequest(BaseModel):
    spotify_client_id: str
    spotify_client_secret: str
    display_name: Optional[str] = None

class UserCredentials(BaseModel):
    user_id: str
    display_name: str
    spotify_client_id: str
    has_credentials: bool
    created_at: str
    last_used: Optional[str] = None

class UserSession(BaseModel):
    user_id: str
    session_token: str
    display_name: str
    spotify_client_id: str
    created_at: str

class VerifiedUserSession(BaseModel):
    user_id: str
    session_token: str
    display_name: str
    spotify_client_id: str
    created_at: str
    # New verification fields
    spotify_verified: bool = False
    spotify_profile: Optional["SpotifyFullProfile"] = None
    anghami_profile: Optional["ProfileData"] = None 