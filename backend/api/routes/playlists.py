"""
Module: Playlist Routes
Purpose: Playlist management endpoints for both Anghami and Spotify
Contains: get_playlists, get_playlist_details, get_anghami_playlists, get_available_playlist_sources
"""

from typing import Optional
from fastapi import APIRouter, HTTPException
from ...core.logging import get_logger
from ...models.anghami_models import AnghamiPlaylist, AnghamiTrack
from ...models.playlist_models import PlaylistFilterRequest
from ...services.anghami_service import get_anghami_playlists_internal, get_anghami_playlists_summary_internal
from ...services.playlist_service import get_available_playlist_sources

logger = get_logger(__name__)
router = APIRouter(prefix="/playlists", tags=["playlists"])

# Import current profile from profiles module
def get_current_profile():
    from .profiles import get_current_profile
    return get_current_profile()

@router.get("")
async def get_playlists():
    """Get user's real Anghami playlists using playlist discoverer"""
    current_profile = get_current_profile()
    
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    try:
        logger.info(f"🎵 Extracting real playlists for profile: {current_profile.display_name}")
        
        # Use the Anghami service to get real playlists
        playlists_data = await get_anghami_playlists_internal(current_profile.profile_url)
        
        # Convert to API format
        api_playlists = []
        
        for playlist in playlists_data["playlists"]:
            api_playlist = AnghamiPlaylist(
                id=playlist["id"],
                name=playlist["name"],
                trackCount=0,  # Will be filled when individual playlist is requested
                duration="Unknown",
                description=playlist.get("description", ""),
                imageUrl=playlist.get("cover_art_url"),
                tracks=[]
            )
            api_playlists.append(api_playlist)
        
        logger.info(f"✅ Returning {len(api_playlists)} real playlists")
        return api_playlists
        
    except Exception as e:
        logger.error(f"❌ Error extracting playlists: {e}")
        # Fallback to indicate error
        return [
            AnghamiPlaylist(
                id="error",
                name=f"❌ Error Loading Playlists",
                trackCount=0,
                duration="N/A",
                description=f"Failed to load playlists from {current_profile.display_name}: {str(e)}",
                imageUrl=None,
                tracks=[]
            )
        ]

@router.get("/{playlist_id}")
async def get_playlist_details(playlist_id: str):
    """Get detailed information about a specific playlist with tracks"""
    current_profile = get_current_profile()
    if not current_profile or not current_profile.is_valid:
        raise HTTPException(status_code=401, detail="No valid profile selected")
    
    try:
        # If it's an error playlist, return mock data
        if playlist_id == "error":
            return AnghamiPlaylist(
                id="error",
                name="❌ Error Loading Playlist",
                trackCount=0,
                duration="N/A",
                description="Failed to load playlist details",
                imageUrl=None,
                tracks=[]
            )
        
        logger.info(f"🎵 Extracting detailed tracks for playlist: {playlist_id}")
        
        # For now, return mock detailed playlist data
        # In real implementation, this would use the direct extractor
        api_tracks = []
        for i in range(10):  # Mock 10 tracks
            api_track = AnghamiTrack(
                id=str(i + 1),
                title=f"Sample Track {i + 1}",
                artist=f"Sample Artist {i + 1}",
                album="Sample Album",
                duration="3:45",
                confidence=1.0
            )
            api_tracks.append(api_track)
        
        # Create detailed playlist response
        detailed_playlist = AnghamiPlaylist(
            id=playlist_id,
            name=f"Sample Playlist {playlist_id}",
            trackCount=len(api_tracks),
            duration=f"{len(api_tracks)} tracks",
            description="Sample playlist description",
            imageUrl=None,
            tracks=api_tracks
        )
        
        logger.info(f"✅ Returning detailed playlist with {len(api_tracks)} tracks")
        return detailed_playlist
        
    except Exception as e:
        logger.error(f"❌ Error extracting playlist details: {e}")
        
        # Return basic playlist info with error indication
        return AnghamiPlaylist(
            id=playlist_id,
            name=f"❌ Error Loading Tracks",
            trackCount=0,
            duration="N/A",
            description=f"Failed to load tracks: {str(e)}",
            imageUrl=None,
            tracks=[]
        )

@router.get("/anghami/summary")
async def get_anghami_playlists_summary(profile_url: Optional[str] = None):
    """Get summary of playlist counts by type"""
    current_profile = get_current_profile()
    target_profile_url = profile_url or (current_profile.profile_url if current_profile else None)
    
    if not target_profile_url:
        raise HTTPException(status_code=400, detail="No profile URL provided and no current profile selected")
    
    try:
        logger.info(f"📊 Getting playlist summary for profile")
        summary = await get_anghami_playlists_summary_internal(target_profile_url)
        return summary
        
    except Exception as e:
        logger.error(f"❌ Error getting playlist summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get playlist summary: {str(e)}")

@router.post("/enhanced")
async def get_enhanced_playlists(filters: PlaylistFilterRequest):
    """Enhanced playlist endpoint that provides both Anghami and Spotify playlists"""
    try:
        logger.info(f"🎵 Getting enhanced playlists with filters: {filters.dict()}")
        
        # For now, return simple response indicating functionality
        return {
            "playlists": [],
            "pagination": {
                "page": filters.page,
                "limit": filters.limit,
                "total": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            },
            "summary": {
                "total_anghami": 0,
                "total_spotify": 0,
                "total_all": 0,
                "displayed": 0
            },
            "filters_applied": filters.dict()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced playlists endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/enhanced/sources")
async def get_available_sources(user_id: Optional[str] = None, anghami_profile_url: Optional[str] = None):
    """Get available playlist sources and their counts"""
    try:
        current_profile = get_current_profile()
        profile_url = anghami_profile_url or (current_profile.profile_url if current_profile else None)
        
        sources = await get_available_playlist_sources(user_id, profile_url)
        return sources
        
    except Exception as e:
        logger.error(f"❌ Error getting available sources: {e}")
        return {"anghami": {"available": False}, "spotify": {"available": False}} 