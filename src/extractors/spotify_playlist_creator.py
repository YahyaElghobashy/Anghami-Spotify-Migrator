#!/usr/bin/env python3
"""
Spotify Playlist Creator & Management

Complete playlist creation system for Anghami to Spotify migration:
- Create Spotify playlists with complete metadata
- Cover art processing and upload (resize, convert format)
- Batch track addition with error handling
- Detailed migration reports
- User review integration for uncertain matches
"""

import asyncio
import json
import time
import base64
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
from datetime import datetime
import logging
from PIL import Image
import requests
import io

# Import from project structure
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.auth.spotify_auth import create_spotify_auth
from src.models.anghami_models import AnghamiPlaylist
from src.extractors.spotify_track_matcher import MatchResult, SpotifyTrackMatch
from src.utils.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class PlaylistCreationResult:
    """Result of playlist creation operation"""
    
    anghami_playlist: AnghamiPlaylist
    spotify_playlist_id: Optional[str] = None
    spotify_playlist_url: Optional[str] = None
    tracks_added: int = 0
    tracks_failed: int = 0
    tracks_skipped_review: int = 0
    cover_art_uploaded: bool = False
    creation_time_ms: int = 0
    error_message: Optional[str] = None
    failed_tracks: List[Dict] = field(default_factory=list)
    review_required_tracks: List[Dict] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Check if playlist creation was successful"""
        return self.spotify_playlist_id is not None
    
    @property
    def total_processed(self) -> int:
        """Total tracks processed"""
        return self.tracks_added + self.tracks_failed + self.tracks_skipped_review


@dataclass_json
@dataclass
class MigrationReport:
    """Complete migration session report"""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    playlists_processed: int = 0
    playlists_created: int = 0
    playlists_failed: int = 0
    total_tracks_processed: int = 0
    total_tracks_added: int = 0
    total_tracks_failed: int = 0
    total_tracks_requiring_review: int = 0
    arabic_tracks_processed: int = 0
    arabic_tracks_added: int = 0
    cover_art_uploads: int = 0
    playlist_results: List[PlaylistCreationResult] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> int:
        """Calculate migration duration"""
        if not self.end_time:
            return 0
        return int((self.end_time - self.start_time).total_seconds())
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate"""
        if self.playlists_processed == 0:
            return 0.0
        return (self.playlists_created / self.playlists_processed) * 100


class CoverArtProcessor:
    """Handles cover art processing and uploading for Spotify playlists"""
    
    @staticmethod
    def download_cover_art(url: str) -> Optional[bytes]:
        """Download cover art from URL"""
        if not url:
            return None
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to download cover art: {e}")
            return None
    
    @staticmethod
    def process_cover_art(image_data: bytes, max_size: int = 256000) -> Optional[str]:
        """Process cover art to meet Spotify requirements and return base64"""
        if not image_data:
            return None
        
        try:
            # Open image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
            
            # Resize to optimal dimensions (max 300x300 for Spotify)
            max_dimension = 300
            if image.width > max_dimension or image.height > max_dimension:
                image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
            
            # Save as JPEG with optimization
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            processed_data = output.getvalue()
            
            # Check size limit
            if len(processed_data) > max_size:
                # Reduce quality if still too large
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=70, optimize=True)
                processed_data = output.getvalue()
            
            # Convert to base64
            base64_data = base64.b64encode(processed_data).decode('utf-8')
            
            logger.info(f"   🖼️ Processed cover art: {len(processed_data)} bytes → base64")
            return base64_data
            
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to process cover art: {e}")
            return None


class SpotifyPlaylistCreator:
    """Advanced Spotify playlist creation and management system"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.spotify_auth = create_spotify_auth()
        self.cover_processor = CoverArtProcessor()
        
        # Configuration
        self.max_batch_size = 100  # Spotify's limit for adding tracks
        self.request_delay = 0.1   # Rate limiting
        
        # Statistics
        self.stats = {
            'playlists_created': 0,
            'playlists_failed': 0,
            'tracks_added': 0,
            'tracks_failed': 0,
            'cover_art_uploads': 0,
            'api_calls': 0
        }
        
        logger.info("🎨 Spotify Playlist Creator initialized")
    
    def authenticate(self) -> bool:
        """Authenticate with Spotify API"""
        logger.info("🔐 Authenticating with Spotify...")
        return self.spotify_auth.authenticate()
    
    async def create_playlist_from_matches(
        self,
        anghami_playlist: AnghamiPlaylist,
        match_results: List[MatchResult],
        skip_user_review: bool = False
    ) -> PlaylistCreationResult:
        """Create Spotify playlist from Anghami playlist and match results"""
        start_time = time.time()
        result = PlaylistCreationResult(anghami_playlist=anghami_playlist)
        
        logger.info(f"🎵 Creating Spotify playlist: '{anghami_playlist.name}'")
        
        try:
            # Step 1: Create the playlist
            playlist_data = await self._create_empty_playlist(anghami_playlist)
            if not playlist_data:
                result.error_message = "Failed to create empty playlist"
                return result
            
            result.spotify_playlist_id = playlist_data['id']
            result.spotify_playlist_url = playlist_data['external_urls']['spotify']
            
            logger.info(f"   ✅ Created playlist: {result.spotify_playlist_url}")
            
            # Step 2: Process matches and collect track URIs
            track_uris, review_tracks = self._process_match_results(match_results, skip_user_review)
            result.tracks_skipped_review = len(review_tracks)
            result.review_required_tracks = review_tracks
            
            # Step 3: Add tracks in batches
            if track_uris:
                added_count, failed_tracks = await self._add_tracks_to_playlist(
                    result.spotify_playlist_id, track_uris
                )
                result.tracks_added = added_count
                result.tracks_failed = len(failed_tracks)
                result.failed_tracks = failed_tracks
                
                logger.info(f"   🎶 Added {added_count} tracks successfully")
            else:
                logger.warning(f"   ⚠️ No tracks to add to playlist")
            
            # Step 4: Upload cover art
            if anghami_playlist.cover_art_url:
                cover_success = await self._upload_cover_art(
                    result.spotify_playlist_id, anghami_playlist.cover_art_url
                )
                result.cover_art_uploaded = cover_success
            
            # Update statistics
            self.stats['playlists_created'] += 1
            self.stats['tracks_added'] += result.tracks_added
            self.stats['tracks_failed'] += result.tracks_failed
            if result.cover_art_uploaded:
                self.stats['cover_art_uploads'] += 1
            
        except Exception as e:
            logger.error(f"   💥 Error creating playlist: {e}")
            result.error_message = str(e)
            self.stats['playlists_failed'] += 1
        
        result.creation_time_ms = int((time.time() - start_time) * 1000)
        return result
    
    async def _create_empty_playlist(self, anghami_playlist: AnghamiPlaylist) -> Optional[Dict]:
        """Create empty Spotify playlist with metadata"""
        try:
            # Get current user ID
            user_response = self.spotify_auth.make_authenticated_request('GET', 'https://api.spotify.com/v1/me')
            user_data = user_response.json()
            user_id = user_data['id']
            
            # Prepare playlist data
            playlist_name = anghami_playlist.name
            description = self._generate_playlist_description(anghami_playlist)
            
            payload = {
                'name': playlist_name,
                'description': description,
                'public': anghami_playlist.is_public,
                'collaborative': False
            }
            
            # Create playlist
            response = self.spotify_auth.make_authenticated_request(
                'POST',
                f'https://api.spotify.com/v1/users/{user_id}/playlists',
                json=payload
            )
            
            self.stats['api_calls'] += 1
            return response.json()
            
        except Exception as e:
            logger.error(f"   💥 Failed to create empty playlist: {e}")
            return None
    
    def _generate_playlist_description(self, anghami_playlist: AnghamiPlaylist) -> str:
        """Generate description for Spotify playlist"""
        description_parts = []
        
        if anghami_playlist.description:
            description_parts.append(anghami_playlist.description)
        
        # Add migration info
        migration_info = f"Migrated from Anghami using Anghami-Spotify-Migrator on {datetime.now().strftime('%Y-%m-%d')}"
        description_parts.append(migration_info)
        
        # Add track count
        track_info = f"Original playlist had {anghami_playlist.track_count} tracks"
        description_parts.append(track_info)
        
        return " | ".join(description_parts)
    
    def _process_match_results(
        self,
        match_results: List[MatchResult],
        skip_user_review: bool = False
    ) -> Tuple[List[str], List[Dict]]:
        """Process match results and return track URIs and review-required tracks"""
        track_uris = []
        review_tracks = []
        
        for result in match_results:
            if not result.has_match:
                # No match found - skip
                continue
            
            if result.requires_user_review and not skip_user_review:
                # Requires user review - collect for later
                review_tracks.append({
                    'anghami_track': result.anghami_track.to_dict(),
                    'spotify_match': result.best_match.to_dict() if result.best_match else None,
                    'confidence': result.match_confidence,
                    'is_arabic': result.is_arabic_track,
                    'reason': 'Low confidence match requiring user approval'
                })
                continue
            
            # Add to playlist
            if result.best_match:
                spotify_uri = f"spotify:track:{result.best_match.spotify_id}"
                track_uris.append(spotify_uri)
        
        logger.info(f"   📋 Processed {len(match_results)} matches:")
        logger.info(f"      ✅ Ready to add: {len(track_uris)}")
        logger.info(f"      ⏸️ Pending review: {len(review_tracks)}")
        
        return track_uris, review_tracks
    
    async def _add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> Tuple[int, List[Dict]]:
        """Add tracks to playlist in batches"""
        if not track_uris:
            return 0, []
        
        added_count = 0
        failed_tracks = []
        
        # Process in batches
        for i in range(0, len(track_uris), self.max_batch_size):
            batch_uris = track_uris[i:i + self.max_batch_size]
            batch_number = (i // self.max_batch_size) + 1
            total_batches = (len(track_uris) + self.max_batch_size - 1) // self.max_batch_size
            
            logger.info(f"   📦 Adding batch {batch_number}/{total_batches} ({len(batch_uris)} tracks)")
            
            try:
                payload = {'uris': batch_uris}
                
                response = self.spotify_auth.make_authenticated_request(
                    'POST',
                    f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
                    json=payload
                )
                
                self.stats['api_calls'] += 1
                added_count += len(batch_uris)
                
                logger.info(f"      ✅ Successfully added {len(batch_uris)} tracks")
                
            except Exception as e:
                logger.error(f"      ❌ Failed to add batch {batch_number}: {e}")
                # Record failed tracks
                for uri in batch_uris:
                    failed_tracks.append({
                        'uri': uri,
                        'error': str(e),
                        'batch': batch_number
                    })
            
            # Rate limiting between batches
            if i + self.max_batch_size < len(track_uris):
                await asyncio.sleep(self.request_delay)
        
        return added_count, failed_tracks
    
    async def _upload_cover_art(self, playlist_id: str, cover_art_url: str) -> bool:
        """Upload cover art to Spotify playlist"""
        try:
            logger.info(f"   🖼️ Processing cover art...")
            
            # Download cover art
            image_data = self.cover_processor.download_cover_art(cover_art_url)
            if not image_data:
                return False
            
            # Process image
            base64_image = self.cover_processor.process_cover_art(image_data)
            if not base64_image:
                return False
            
            # Upload to Spotify
            response = self.spotify_auth.make_authenticated_request(
                'PUT',
                f'https://api.spotify.com/v1/playlists/{playlist_id}/images',
                data=base64_image,
                headers={
                    'Authorization': f'Bearer {self.spotify_auth.access_token}',
                    'Content-Type': 'image/jpeg'
                }
            )
            
            self.stats['api_calls'] += 1
            logger.info(f"   🎨 Cover art uploaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"   ⚠️ Failed to upload cover art: {e}")
            return False
    
    async def migrate_playlists(
        self,
        playlists_with_matches: List[Tuple[AnghamiPlaylist, List[MatchResult]]],
        skip_user_review: bool = False
    ) -> MigrationReport:
        """Migrate multiple playlists to Spotify"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = MigrationReport(
            session_id=session_id,
            start_time=datetime.now()
        )
        
        logger.info(f"🚀 Starting playlist migration session: {session_id}")
        logger.info(f"📝 Processing {len(playlists_with_matches)} playlists")
        
        for i, (anghami_playlist, match_results) in enumerate(playlists_with_matches, 1):
            logger.info(f"\n🎵 Processing playlist {i}/{len(playlists_with_matches)}: '{anghami_playlist.name}'")
            
            # Create playlist
            creation_result = await self.create_playlist_from_matches(
                anghami_playlist, match_results, skip_user_review
            )
            
            # Update report
            report.playlist_results.append(creation_result)
            report.playlists_processed += 1
            
            if creation_result.success:
                report.playlists_created += 1
                logger.info(f"   ✅ Successfully created: {creation_result.spotify_playlist_url}")
            else:
                report.playlists_failed += 1
                logger.error(f"   ❌ Failed to create playlist: {creation_result.error_message}")
            
            # Update statistics
            report.total_tracks_processed += creation_result.total_processed
            report.total_tracks_added += creation_result.tracks_added
            report.total_tracks_failed += creation_result.tracks_failed
            report.total_tracks_requiring_review += creation_result.tracks_skipped_review
            
            # Count Arabic tracks
            arabic_count = sum(1 for mr in match_results if mr.is_arabic_track)
            arabic_added = sum(1 for mr in match_results 
                             if mr.is_arabic_track and mr.has_match and not mr.requires_user_review)
            
            report.arabic_tracks_processed += arabic_count
            report.arabic_tracks_added += arabic_added
            
            if creation_result.cover_art_uploaded:
                report.cover_art_uploads += 1
            
            # Small delay between playlists
            if i < len(playlists_with_matches):
                await asyncio.sleep(1)
        
        # Finalize report
        report.end_time = datetime.now()
        
        # Generate final summary
        await self._generate_migration_summary(report)
        
        return report
    
    async def _generate_migration_summary(self, report: MigrationReport):
        """Generate and display final migration summary"""
        duration = report.duration_seconds
        
        summary = f"""
🎉 Migration Session Complete!

📊 SESSION SUMMARY:
{'='*60}
Session ID: {report.session_id}
Duration: {duration // 60}m {duration % 60}s
Start Time: {report.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {report.end_time.strftime('%Y-%m-%d %H:%M:%S')}

🎵 PLAYLIST RESULTS:
{'='*60}
✅ Playlists Created: {report.playlists_created}/{report.playlists_processed}
❌ Playlists Failed: {report.playlists_failed}
📈 Success Rate: {report.success_rate:.1f}%

🎶 TRACK STATISTICS:
{'='*60}
📀 Total Tracks Processed: {report.total_tracks_processed}
✅ Tracks Added: {report.total_tracks_added}
❌ Tracks Failed: {report.total_tracks_failed}
⏸️ Tracks Requiring Review: {report.total_tracks_requiring_review}

🌍 ARABIC TRACK PERFORMANCE:
{'='*60}
📀 Arabic Tracks Processed: {report.arabic_tracks_processed}
✅ Arabic Tracks Added: {report.arabic_tracks_added}
📈 Arabic Success Rate: {(report.arabic_tracks_added/report.arabic_tracks_processed*100) if report.arabic_tracks_processed > 0 else 0:.1f}%

🎨 ADDITIONAL FEATURES:
{'='*60}
🖼️ Cover Art Uploads: {report.cover_art_uploads}
🌐 API Calls Made: {self.stats['api_calls']}
"""
        
        print(summary)
        logger.info("Migration session completed successfully")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get creator statistics"""
        return {
            'creator_stats': self.stats,
            'configuration': {
                'max_batch_size': self.max_batch_size,
                'request_delay': self.request_delay
            }
        }
    
    def save_migration_report(self, report: MigrationReport, output_file: Path) -> None:
        """Save detailed migration report to JSON file"""
        try:
            report_data = report.to_dict()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 Migration report saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save migration report: {e}")


async def main():
    """Test the Spotify playlist creator"""
    import sys
    
    creator = SpotifyPlaylistCreator()
    
    print("🎨 Spotify Playlist Creator - Test Mode")
    print("=" * 60)
    
    # Authenticate
    if not creator.authenticate():
        print("❌ Authentication failed")
        return
    
    print("✅ Ready to create playlists!")
    print("📝 This test mode requires matching results from the track matcher.")
    print("🎯 Run the track matcher first to generate matching data.")


if __name__ == "__main__":
    asyncio.run(main()) 