"""
Module: Anghami Models
Purpose: Pydantic models for Anghami profile and playlist data
Contains: ProfileValidationRequest, ProfileData, ProfileHistoryItem, AnghamiTrack, AnghamiPlaylist
"""

from typing import Optional, List, Dict
from pydantic import BaseModel

class ProfileValidationRequest(BaseModel):
    profile_url: str

class ProfileData(BaseModel):
    profile_url: str
    profile_id: str
    display_name: str
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    most_played_songs: Optional[List[Dict]] = None
    is_valid: bool
    error_message: Optional[str] = None

class ProfileHistoryItem(BaseModel):
    id: int
    profile_url: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    follower_count: Optional[int] = None
    usage_count: int
    last_used: str

class AnghamiTrack(BaseModel):
    id: str
    title: str
    artist: str
    album: Optional[str] = None
    duration: Optional[str] = None
    confidence: Optional[float] = None
    spotifyMatch: Optional[Dict] = None

class AnghamiPlaylist(BaseModel):
    id: str
    name: str
    trackCount: int
    duration: str
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    tracks: Optional[List[AnghamiTrack]] = None 