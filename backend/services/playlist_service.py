"""
Module: Playlist Service  
Purpose: Unified playlist management across Anghami and Spotify sources
"""

from typing import List, Optional
from ..core.logging import get_logger
from ..models.playlist_models import PlaylistFilterRequest

logger = get_logger(__name__)

async def get_available_playlist_sources(user_id: Optional[str] = None, anghami_profile_url: Optional[str] = None):
    """Get available playlist sources and their counts"""
    try:
        sources = {}
        
        # Check Anghami availability
        if anghami_profile_url:
            sources["anghami"] = {"available": True}
        else:
            sources["anghami"] = {"available": False, "error": "No Anghami profile selected"}
        
        # Check Spotify availability
        if user_id:
            sources["spotify"] = {"available": True}
        else:
            sources["spotify"] = {"available": False, "error": "No Spotify user authenticated"}
        
        return sources
        
    except Exception as e:
        logger.error(f"❌ Error getting available sources: {e}")
        return {"anghami": {"available": False}, "spotify": {"available": False}} 