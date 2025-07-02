"""
Module: Anghami Service
Purpose: Business logic for Anghami profile and playlist operations
Contains: validate_anghami_profile_url, extract_profile_id, fetch_anghami_profile_data, 
         get_anghami_playlists_internal, get_anghami_playlists_summary_internal
"""

import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from ..core.logging import get_logger
from ..models.anghami_models import ProfileData

# Import existing extractors
sys.path.append(str(Path(__file__).parent.parent.parent / "src" / "extractors"))
from anghami_profile_extractor import AnghamiProfileExtractor
from anghami_user_playlist_discoverer import AnghamiUserPlaylistDiscoverer

logger = get_logger(__name__)

def validate_anghami_profile_url(url: str) -> bool:
    """Validate if URL is a valid Anghami profile URL"""
    try:
        parsed = urlparse(url)
        return (
            parsed.netloc in ['play.anghami.com', 'anghami.com', 'www.anghami.com'] and
            '/profile/' in parsed.path
        )
    except:
        return False

def extract_profile_id(url: str) -> Optional[str]:
    """Extract profile ID from Anghami URL"""
    try:
        parsed = urlparse(url)
        if '/profile/' in parsed.path:
            return parsed.path.split('/profile/')[-1].split('?')[0].split('/')[0]
    except:
        pass
    return None

async def fetch_anghami_profile_data(profile_url: str) -> ProfileData:
    """Fetch profile data from Anghami using the profile extractor"""
    try:
        profile_extractor = AnghamiProfileExtractor()
        
        # Extract real profile data from Anghami
        profile_data = await profile_extractor.extract_profile_data(profile_url)
        
        return ProfileData(
            profile_url=profile_data["profile_url"],
            profile_id=profile_data.get("profile_id", extract_profile_id(profile_url) or "unknown"),
            display_name=profile_data.get("display_name", "Unknown User"),
            avatar_url=profile_data.get("avatar_url"),
            follower_count=profile_data.get("follower_count"),
            most_played_songs=profile_data.get("most_played_songs"),
            is_valid=profile_data.get("is_valid", False),
            error_message=profile_data.get("error_message")
        )
        
    except Exception as e:
        logger.error(f"Error fetching profile data: {e}")
        return ProfileData(
            profile_url=profile_url,
            profile_id=extract_profile_id(profile_url) or "unknown",
            display_name="Unknown User",
            avatar_url=None,
            follower_count=0,
            most_played_songs=[],
            is_valid=False,
            error_message=f"Failed to fetch profile data: {str(e)}"
        )

async def get_anghami_playlists_internal(profile_url: str, type: str = "all", page: int = 1, limit: int = 20):
    """Internal function to get Anghami playlists"""
    try:
        logger.info(f"🎵 Extracting real playlists for profile: {profile_url}")
        
        # Use the playlist discoverer to get real playlists
        discoverer = AnghamiUserPlaylistDiscoverer()
        user_playlists = await discoverer.discover_user_playlists(profile_url)
        
        # Filter by type
        filtered_playlists = []
        if type in ["all", "created"]:
            filtered_playlists.extend(user_playlists.created_playlists)
        if type in ["all", "followed"]:
            filtered_playlists.extend(user_playlists.followed_playlists)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_playlists = filtered_playlists[start_idx:end_idx]
        
        # Convert to API format
        api_playlists = []
        for playlist in paginated_playlists:
            indicator = "🎵" if playlist.playlist_type == "created" else "➕"
            api_playlist = {
                "id": playlist.id,
                "name": f"{indicator} {playlist.name}",
                "type": playlist.playlist_type,
                "url": playlist.url,
                "description": playlist.description,
                "cover_art_url": playlist.cover_art_url
            }
            api_playlists.append(api_playlist)
        
        return {
            "playlists": api_playlists,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": len(filtered_playlists),
                "total_pages": (len(filtered_playlists) + limit - 1) // limit,
                "has_next": end_idx < len(filtered_playlists),
                "has_prev": page > 1
            },
            "summary": {
                "total_created": user_playlists.total_created,
                "total_followed": user_playlists.total_followed,
                "total_all": user_playlists.total_created + user_playlists.total_followed,
                "filter_applied": type
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting Anghami playlists: {e}")
        raise

async def get_anghami_playlists_summary_internal(profile_url: str):
    """Internal function to get Anghami playlists summary"""
    try:
        logger.info(f"📊 Getting playlist summary for profile")
        
        discoverer = AnghamiUserPlaylistDiscoverer()
        user_playlists = await discoverer.discover_user_playlists(profile_url)
        
        return {
            "profile_url": profile_url,
            "user_id": user_playlists.user_id,
            "created_playlists": user_playlists.total_created,
            "followed_playlists": user_playlists.total_followed,
            "total_playlists": user_playlists.total_created + user_playlists.total_followed,
            "extraction_timestamp": user_playlists.extracted_at if hasattr(user_playlists, 'extracted_at') else None
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting playlist summary: {e}")
        raise 