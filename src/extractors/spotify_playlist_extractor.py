#!/usr/bin/env python3
"""
Spotify Playlist Extractor using Spotify Web API
Retrieves user playlists, metadata, tracks, and cover art from Spotify
Follows same patterns as anghami_direct_extractor.py for consistency
"""

import asyncio
import json
import os
import time
import requests
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

# Import from new structure (following anghami_direct_extractor pattern)
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.models.spotify_models import SpotifyPlaylist, SpotifyTrack, SpotifyUserPlaylists
from src.utils.config import get_config

# Setup logging (same as anghami extractor)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SpotifyPlaylistExtractor:
    def __init__(self, config=None):
        self.config = config or get_config()
        
        # Use configured directories (same pattern as anghami extractor)
        self.output_dir = self.config.directories.playlists_dir
        self.cover_art_dir = self.config.directories.cover_art_dir
        self.cache_dir = self.config.directories.temp_dir / "spotify_cache"
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cover_art_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Spotify API endpoints
        self.api_base = "https://api.spotify.com/v1"
        self.access_token = None
        
    def set_access_token(self, access_token: str):
        """Set the Spotify access token for API requests"""
        self.access_token = access_token
    
    async def extract_user_playlists(self, user_id: str, include_followed: bool = True, 
                                   include_tracks: bool = False) -> SpotifyUserPlaylists:
        """Extract all playlists for a user (following anghami extractor pattern)"""
        logger.info(f"Starting Spotify playlist extraction for user: {user_id}")
        
        if not self.access_token:
            raise ValueError("Spotify access token not set. Call set_access_token() first.")
        
        try:
            # Get user profile info
            user_profile = await self._get_user_profile(user_id)
            
            # Get owned playlists (created by user)
            logger.info("Extracting owned playlists...")
            owned_playlists = await self._get_owned_playlists(user_id, include_tracks)
            
            # Get followed playlists (if requested)
            followed_playlists = []
            if include_followed:
                logger.info("Extracting followed playlists...")
                followed_playlists = await self._get_followed_playlists(user_id, include_tracks)
            
            # Create container object (following anghami pattern)
            user_playlists = SpotifyUserPlaylists(
                user_id=user_id,
                display_name=user_profile.get("display_name"),
                owned_playlists=owned_playlists,
                followed_playlists=followed_playlists
            )
            
            # Save to file (following anghami extractor pattern)
            await self._save_user_playlists(user_playlists)
            
            logger.info(f"✅ Spotify extraction completed! "
                       f"Owned: {len(owned_playlists)}, Followed: {len(followed_playlists)}")
            
            return user_playlists
            
        except Exception as e:
            logger.error(f"Error extracting Spotify playlists: {e}")
            raise
    
    async def extract_playlist_details(self, playlist_id: str, include_tracks: bool = True) -> SpotifyPlaylist:
        """Extract detailed information about a specific playlist"""
        logger.info(f"Extracting detailed information for playlist: {playlist_id}")
        
        try:
            # Get playlist metadata
            playlist_data = await self._get_playlist_metadata(playlist_id)
            
            # Get tracks if requested
            tracks = []
            if include_tracks:
                tracks = await self._get_playlist_tracks(playlist_id)
            
            # Create playlist object
            playlist = SpotifyPlaylist(
                id=playlist_data["id"],
                name=playlist_data["name"],
                description=playlist_data.get("description", ""),
                owner_id=playlist_data["owner"]["id"],
                owner_name=playlist_data["owner"]["display_name"],
                is_public=playlist_data.get("public", True),
                is_collaborative=playlist_data.get("collaborative", False),
                track_count=playlist_data["tracks"]["total"],
                follower_count=playlist_data.get("followers", {}).get("total"),
                cover_art_url=self._get_cover_art_url(playlist_data),
                external_url=playlist_data["external_urls"].get("spotify"),
                tracks=tracks
            )
            
            # Download cover art (following anghami pattern)
            if playlist.cover_art_url:
                cover_filename = await self._download_cover_art(playlist.cover_art_url, playlist.id)
                if cover_filename:
                    playlist.cover_art_local_path = cover_filename
            
            logger.info(f"✅ Playlist details extracted: '{playlist.name}' with {len(tracks)} tracks")
            return playlist
            
        except Exception as e:
            logger.error(f"Error extracting playlist details: {e}")
            raise
    
    async def _get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile information"""
        try:
            # Try to get current user if user_id is 'me' or matches current user
            if user_id == "me":
                response = await self._make_api_request(f"{self.api_base}/me")
            else:
                response = await self._make_api_request(f"{self.api_base}/users/{user_id}")
            
            return response
        except Exception as e:
            logger.warning(f"Could not get user profile: {e}")
            return {"display_name": user_id, "id": user_id}
    
    async def _get_owned_playlists(self, user_id: str, include_tracks: bool = False) -> List[SpotifyPlaylist]:
        """Get playlists owned by the user"""
        playlists = []
        
        try:
            # Get current user's actual ID if using "me"
            actual_user_id = user_id
            if user_id == "me":
                user_profile = await self._get_user_profile("me")
                actual_user_id = user_profile.get("id", user_id)
            
            # Get all user playlists with pagination
            url = f"{self.api_base}/me/playlists" if user_id == "me" else f"{self.api_base}/users/{user_id}/playlists"
            all_playlists = await self._get_paginated_results(url)
            
            # Filter for owned playlists only
            for playlist_data in all_playlists:
                playlist_owner_id = playlist_data["owner"]["id"]
                if playlist_owner_id == actual_user_id:
                    playlist = await self._create_playlist_object(playlist_data, include_tracks, is_owned=True)
                    playlists.append(playlist)
            
        except Exception as e:
            logger.error(f"Error getting owned playlists: {e}")
        
        return playlists
    
    async def _get_followed_playlists(self, user_id: str, include_tracks: bool = False) -> List[SpotifyPlaylist]:
        """Get playlists followed by the user"""
        playlists = []
        
        try:
            # Get current user's actual ID if using "me"
            actual_user_id = user_id
            if user_id == "me":
                user_profile = await self._get_user_profile("me")
                actual_user_id = user_profile.get("id", user_id)
            
            # Get all user playlists with pagination
            url = f"{self.api_base}/me/playlists" if user_id == "me" else f"{self.api_base}/users/{user_id}/playlists"
            all_playlists = await self._get_paginated_results(url)
            
            # Filter for followed playlists only (not owned by user)
            for playlist_data in all_playlists:
                playlist_owner_id = playlist_data["owner"]["id"]
                if playlist_owner_id != actual_user_id:
                    playlist = await self._create_playlist_object(playlist_data, include_tracks, is_followed=True)
                    playlists.append(playlist)
            
        except Exception as e:
            logger.error(f"Error getting followed playlists: {e}")
        
        return playlists
    
    async def _create_playlist_object(self, playlist_data: Dict[str, Any], 
                                    include_tracks: bool = False, 
                                    is_owned: bool = False, 
                                    is_followed: bool = False) -> SpotifyPlaylist:
        """Create SpotifyPlaylist object from API data"""
        
        # Get tracks if requested
        tracks = []
        if include_tracks:
            tracks = await self._get_playlist_tracks(playlist_data["id"])
        
        return SpotifyPlaylist(
            id=playlist_data["id"],
            name=playlist_data["name"],
            description=playlist_data.get("description", ""),
            owner_id=playlist_data["owner"]["id"],
            owner_name=playlist_data["owner"].get("display_name", ""),
            is_owned=is_owned,
            is_followed=is_followed,
            is_public=playlist_data.get("public", True),
            is_collaborative=playlist_data.get("collaborative", False),
            track_count=playlist_data["tracks"]["total"],
            follower_count=playlist_data.get("followers", {}).get("total"),
            cover_art_url=self._get_cover_art_url(playlist_data),
            external_url=playlist_data["external_urls"].get("spotify"),
            tracks=tracks
        )
    
    async def _get_playlist_metadata(self, playlist_id: str) -> Dict[str, Any]:
        """Get playlist metadata from Spotify API"""
        url = f"{self.api_base}/playlists/{playlist_id}"
        return await self._make_api_request(url)
    
    async def _get_playlist_tracks(self, playlist_id: str) -> List[SpotifyTrack]:
        """Get all tracks from a playlist with pagination"""
        tracks = []
        
        try:
            url = f"{self.api_base}/playlists/{playlist_id}/tracks"
            all_track_items = await self._get_paginated_results(url)
            
            for item in all_track_items:
                if item.get("track") and item["track"].get("id"):
                    track_data = item["track"]
                    
                    # Create SpotifyTrack object
                    track = SpotifyTrack(
                        id=track_data["id"],
                        title=track_data["name"],
                        artists=[artist["name"] for artist in track_data.get("artists", [])],
                        album=track_data.get("album", {}).get("name"),
                        duration_ms=track_data.get("duration_ms"),
                        preview_url=track_data.get("preview_url"),
                        external_url=track_data.get("external_urls", {}).get("spotify"),
                        track_number=track_data.get("track_number"),
                        explicit=track_data.get("explicit", False),
                        popularity=track_data.get("popularity"),
                        added_at=item.get("added_at"),
                        added_by=item.get("added_by", {}).get("id") if item.get("added_by") else None
                    )
                    tracks.append(track)
            
            logger.info(f"Extracted {len(tracks)} tracks from playlist {playlist_id}")
            
        except Exception as e:
            logger.error(f"Error getting playlist tracks: {e}")
        
        return tracks
    
    async def _get_paginated_results(self, url: str) -> List[Dict[str, Any]]:
        """Handle Spotify API pagination (similar to scrolling in anghami extractor)"""
        all_items = []
        next_url = url
        
        while next_url:
            try:
                response = await self._make_api_request(next_url)
                items = response.get("items", [])
                all_items.extend(items)
                
                next_url = response.get("next")
                
                if next_url:
                    logger.debug(f"Fetching next page... (total items so far: {len(all_items)})")
                
            except Exception as e:
                logger.error(f"Error in pagination: {e}")
                break
        
        logger.info(f"Retrieved {len(all_items)} total items from paginated endpoint")
        return all_items
    
    async def _make_api_request(self, url: str) -> Dict[str, Any]:
        """Make authenticated request to Spotify API"""
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Spotify API request failed: {e}")
            raise
    
    def _get_cover_art_url(self, playlist_data: Dict[str, Any]) -> Optional[str]:
        """Extract cover art URL from playlist data"""
        images = playlist_data.get("images", [])
        if images:
            # Return the highest quality image (first one is usually highest)
            return images[0].get("url")
        return None
    
    async def _download_cover_art(self, cover_url: str, playlist_id: str) -> str:
        """Download cover art image (following anghami extractor pattern)"""
        try:
            response = requests.get(cover_url, headers={
                'User-Agent': self.config.extractor.user_agent
            })
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'png' in content_type:
                ext = 'png'
            elif 'webp' in content_type:
                ext = 'webp'
            else:
                ext = 'jpg'  # Default
            
            filename = f"spotify_cover_{playlist_id}.{ext}"
            filepath = self.cover_art_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Cover art downloaded: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to download cover art: {e}")
            return ""
    
    async def _save_user_playlists(self, user_playlists: SpotifyUserPlaylists, save_to_file: bool = True):
        """Save user playlists to file (following anghami extractor pattern)"""
        if not save_to_file:
            return
        
        try:
            timestamp = int(time.time())
            filename = f"spotify_playlists_{user_playlists.user_id}_{timestamp}.json"
            filepath = self.output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(user_playlists.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.info(f"Spotify playlists saved to: {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving playlists to file: {e}")

async def main():
    """Main function to test the extractor (following anghami pattern)"""
    import sys
    
    extractor = SpotifyPlaylistExtractor()
    
    # Get access token from command line or prompt user
    if len(sys.argv) > 1:
        access_token = sys.argv[1]
    else:
        access_token = input("Enter Spotify access token: ").strip()
        if not access_token:
            print("❌ No access token provided")
            return
    
    extractor.set_access_token(access_token)
    
    try:
        user_playlists = await extractor.extract_user_playlists(
            user_id="me", 
            include_followed=True, 
            include_tracks=True
        )
        
        print(f"\n✅ Spotify playlist extraction completed!")
        print(f"👤 User: {user_playlists.display_name}")
        print(f"🎵 Owned playlists: {user_playlists.total_owned}")
        print(f"➕ Followed playlists: {user_playlists.total_followed}")
        print(f"📊 Total playlists: {user_playlists.total_playlists}")
        
        # Print sample playlists
        if user_playlists.owned_playlists:
            print(f"\n🎶 Sample owned playlists:")
            for i, playlist in enumerate(user_playlists.owned_playlists[:5]):
                print(f"  {i+1}. {playlist.name} ({playlist.track_count} tracks)")
        
        if user_playlists.followed_playlists:
            print(f"\n➕ Sample followed playlists:")
            for i, playlist in enumerate(user_playlists.followed_playlists[:5]):
                print(f"  {i+1}. {playlist.name} by {playlist.owner_name} ({playlist.track_count} tracks)")
                
        print(f"\n📁 Data saved to: data/playlists/spotify_playlists_*.json")
        
    except Exception as e:
        print(f"❌ Spotify extraction failed: {e}")
        print("💡 Make sure you have a valid Spotify access token.")

if __name__ == "__main__":
    asyncio.run(main()) 