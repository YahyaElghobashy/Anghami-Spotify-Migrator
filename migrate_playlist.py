#!/usr/bin/env python3
"""
Complete Anghami to Spotify Migration Tool

End-to-end workflow: Extract → Match → Create → Report
- Load Anghami playlist data
- Match tracks using enhanced Arabic-aware engine
- Create Spotify playlists with metadata and cover art
- Generate comprehensive migration reports
- Support user review for uncertain matches
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Tuple
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.extractors.spotify_track_matcher import SpotifyTrackMatcher, MatchResult
from src.extractors.spotify_playlist_creator import SpotifyPlaylistCreator, MigrationReport
from src.models.anghami_models import AnghamiPlaylist
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CompleteMigrationTool:
    """Complete Anghami to Spotify migration workflow"""
    
    def __init__(self):
        self.track_matcher = SpotifyTrackMatcher()
        self.playlist_creator = SpotifyPlaylistCreator()
        
        # Directories
        self.data_dir = Path("data")
        self.playlists_dir = self.data_dir / "playlists"
        self.reports_dir = self.data_dir / "migration_reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 Complete Anghami → Spotify Migration Tool")
        print("=" * 60)
    
    def authenticate(self) -> bool:
        """Authenticate with Spotify"""
        print("🔐 Authenticating with Spotify...")
        success = self.track_matcher.authenticate()
        if success:
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed")
        return success
    
    def load_playlist_data(self, playlist_file: Path) -> AnghamiPlaylist:
        """Load Anghami playlist from JSON file"""
        try:
            with open(playlist_file, 'r', encoding='utf-8') as f:
                playlist_data = json.load(f)
            
            anghami_playlist = AnghamiPlaylist.from_dict(playlist_data)
            print(f"📀 Loaded playlist: '{anghami_playlist.name}' ({len(anghami_playlist.tracks)} tracks)")
            return anghami_playlist
            
        except Exception as e:
            print(f"❌ Failed to load playlist: {e}")
            sys.exit(1)
    
    def find_available_playlists(self) -> List[Path]:
        """Find all available playlist JSON files"""
        if not self.playlists_dir.exists():
            return []
        
        playlist_files = list(self.playlists_dir.glob("playlist_*_direct.json"))
        return sorted(playlist_files)
    
    async def match_playlist_tracks(
        self, 
        anghami_playlist: AnghamiPlaylist,
        save_results: bool = True
    ) -> List[MatchResult]:
        """Match all tracks in playlist using enhanced Arabic engine"""
        print(f"\n🎯 Starting track matching for '{anghami_playlist.name}'...")
        
        # Match tracks
        match_results = await self.track_matcher.match_playlist(anghami_playlist)
        
        # Save detailed matching results
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            matching_file = self.reports_dir / f"matching_{anghami_playlist.id}_{timestamp}.json"
            self.track_matcher.save_results(match_results, matching_file)
            print(f"💾 Matching results saved: {matching_file}")
        
        return match_results
    
    async def create_spotify_playlist(
        self,
        anghami_playlist: AnghamiPlaylist,
        match_results: List[MatchResult],
        skip_user_review: bool = False
    ) -> None:
        """Create Spotify playlist from matches"""
        print(f"\n🎨 Creating Spotify playlist...")
        
        # Create playlist
        creation_result = await self.playlist_creator.create_playlist_from_matches(
            anghami_playlist, match_results, skip_user_review
        )
        
        if creation_result.success:
            print(f"✅ Successfully created playlist!")
            print(f"🔗 Spotify URL: {creation_result.spotify_playlist_url}")
            print(f"🎶 Tracks added: {creation_result.tracks_added}")
            
            if creation_result.tracks_skipped_review > 0:
                print(f"⏸️ Tracks requiring review: {creation_result.tracks_skipped_review}")
            
            if creation_result.cover_art_uploaded:
                print(f"🎨 Cover art uploaded successfully")
        else:
            print(f"❌ Failed to create playlist: {creation_result.error_message}")
        
        return creation_result
    
    async def migrate_single_playlist(
        self,
        playlist_file: Path,
        skip_user_review: bool = False
    ) -> None:
        """Complete migration workflow for a single playlist"""
        print(f"\n{'='*60}")
        print(f"🎵 MIGRATING PLAYLIST: {playlist_file.name}")
        print(f"{'='*60}")
        
        # Step 1: Load playlist data
        anghami_playlist = self.load_playlist_data(playlist_file)
        
        # Step 2: Match tracks
        match_results = await self.match_playlist_tracks(anghami_playlist)
        
        # Step 3: Show matching summary
        self.show_matching_summary(match_results)
        
        # Step 4: Ask user about review tracks (if any)
        if not skip_user_review:
            review_tracks = [r for r in match_results if r.requires_user_review]
            if review_tracks:
                skip_user_review = self.handle_user_review_prompt(review_tracks)
        
        # Step 5: Create Spotify playlist
        creation_result = await self.create_spotify_playlist(
            anghami_playlist, match_results, skip_user_review
        )
        
        # Step 6: Save complete migration report
        self.save_single_playlist_report(anghami_playlist, match_results, creation_result)
        
        print(f"\n✅ Migration complete for '{anghami_playlist.name}'!")
    
    def show_matching_summary(self, match_results: List[MatchResult]) -> None:
        """Show detailed matching summary"""
        total = len(match_results)
        matched = sum(1 for r in match_results if r.has_match)
        confident = sum(1 for r in match_results if r.has_confident_match)
        arabic = sum(1 for r in match_results if r.is_arabic_track)
        review_needed = sum(1 for r in match_results if r.requires_user_review)
        
        print(f"\n📊 MATCHING SUMMARY:")
        print(f"   📀 Total tracks: {total}")
        print(f"   ✅ Matches found: {matched}/{total} ({matched/total*100:.1f}%)")
        print(f"   🎯 High confidence: {confident}/{total} ({confident/total*100:.1f}%)")
        print(f"   🌍 Arabic tracks: {arabic}/{total} ({arabic/total*100:.1f}%)")
        print(f"   ⚠️ Requiring review: {review_needed}/{total} ({review_needed/total*100:.1f}%)")
    
    def handle_user_review_prompt(self, review_tracks: List[MatchResult]) -> bool:
        """Ask user about tracks requiring review"""
        print(f"\n⚠️ {len(review_tracks)} tracks require user review due to low confidence matches:")
        
        for i, result in enumerate(review_tracks[:5], 1):  # Show first 5
            confidence = result.match_confidence
            anghami = f"'{result.anghami_track.title}' by {result.anghami_track.primary_artist}"
            spotify = f"'{result.best_match.title}' by {result.best_match.primary_artist}" if result.best_match else "No match"
            print(f"   {i}. {anghami} → {spotify} (confidence: {confidence:.2f})")
        
        if len(review_tracks) > 5:
            print(f"   ... and {len(review_tracks) - 5} more")
        
        print(f"\nOptions:")
        print(f"1. Skip review tracks for now (recommended for first run)")
        print(f"2. Include all tracks anyway (not recommended)")
        
        while True:
            try:
                choice = input("Choose option (1 or 2): ").strip()
                if choice == "1":
                    print("⏸️ Review tracks will be skipped")
                    return False  # Don't skip user review
                elif choice == "2":
                    print("⚠️ Including all tracks (low confidence matches may be incorrect)")
                    return True   # Skip user review
                else:
                    print("Please enter 1 or 2")
            except KeyboardInterrupt:
                print("\n❌ Migration cancelled by user")
                sys.exit(0)
    
    def save_single_playlist_report(
        self,
        anghami_playlist: AnghamiPlaylist,
        match_results: List[MatchResult],
        creation_result
    ) -> None:
        """Save complete report for single playlist migration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"migration_{anghami_playlist.id}_{timestamp}.json"
        
        report_data = {
            "migration_session": {
                "timestamp": datetime.now().isoformat(),
                "playlist_id": anghami_playlist.id,
                "playlist_name": anghami_playlist.name,
                "total_tracks": len(anghami_playlist.tracks)
            },
            "anghami_playlist": anghami_playlist.to_dict(),
            "matching_results": [r.to_dict() for r in match_results],
            "creation_result": creation_result.to_dict() if creation_result else None,
            "statistics": {
                "tracks_matched": sum(1 for r in match_results if r.has_match),
                "tracks_confident": sum(1 for r in match_results if r.has_confident_match),
                "tracks_arabic": sum(1 for r in match_results if r.is_arabic_track),
                "tracks_review": sum(1 for r in match_results if r.requires_user_review),
                "tracks_added": creation_result.tracks_added if creation_result else 0
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 Complete migration report saved: {report_file}")
        except Exception as e:
            print(f"⚠️ Failed to save migration report: {e}")
    
    async def migrate_multiple_playlists(
        self,
        playlist_files: List[Path],
        skip_user_review: bool = False
    ) -> None:
        """Migrate multiple playlists in batch"""
        print(f"\n{'='*60}")
        print(f"🚀 BATCH MIGRATION: {len(playlist_files)} playlists")
        print(f"{'='*60}")
        
        # Load all playlists and match tracks
        playlists_with_matches = []
        
        for i, playlist_file in enumerate(playlist_files, 1):
            print(f"\n📀 Processing playlist {i}/{len(playlist_files)}: {playlist_file.name}")
            
            # Load and match
            anghami_playlist = self.load_playlist_data(playlist_file)
            match_results = await self.match_playlist_tracks(anghami_playlist, save_results=False)
            
            playlists_with_matches.append((anghami_playlist, match_results))
        
        # Create all playlists
        print(f"\n🎨 Creating {len(playlists_with_matches)} Spotify playlists...")
        migration_report = await self.playlist_creator.migrate_playlists(
            playlists_with_matches, skip_user_review
        )
        
        # Save comprehensive report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f"batch_migration_{timestamp}.json"
        self.playlist_creator.save_migration_report(migration_report, report_file)
        
        print(f"\n🎉 Batch migration complete!")
        print(f"📄 Comprehensive report saved: {report_file}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Complete Anghami to Spotify Migration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate a specific playlist
  python migrate_playlist.py --playlist data/playlists/playlist_123_direct.json
  
  # Migrate all available playlists
  python migrate_playlist.py --all
  
  # Skip user review prompts (auto-include uncertain matches)
  python migrate_playlist.py --playlist data/playlists/playlist_123_direct.json --skip-review
        """
    )
    
    parser.add_argument(
        '--playlist', '-p',
        type=Path,
        help='Path to specific playlist JSON file'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Migrate all available playlists'
    )
    
    parser.add_argument(
        '--skip-review', '-s',
        action='store_true',
        help='Skip user review prompts (include all matches)'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available playlists'
    )
    
    args = parser.parse_args()
    
    # Create migration tool
    migration_tool = CompleteMigrationTool()
    
    # List available playlists
    if args.list:
        playlists = migration_tool.find_available_playlists()
        if playlists:
            print("📋 Available playlists:")
            for i, playlist_file in enumerate(playlists, 1):
                print(f"   {i}. {playlist_file.name}")
        else:
            print("❌ No playlist files found in data/playlists/")
        return
    
    # Authenticate with Spotify
    if not migration_tool.authenticate():
        return
    
    async def run_migration():
        if args.playlist:
            # Single playlist migration
            if not args.playlist.exists():
                print(f"❌ Playlist file not found: {args.playlist}")
                return
            
            await migration_tool.migrate_single_playlist(
                args.playlist,
                skip_user_review=args.skip_review
            )
            
        elif args.all:
            # Batch migration
            playlists = migration_tool.find_available_playlists()
            if not playlists:
                print("❌ No playlist files found in data/playlists/")
                return
            
            await migration_tool.migrate_multiple_playlists(
                playlists,
                skip_user_review=args.skip_review
            )
            
        else:
            # Interactive mode
            playlists = migration_tool.find_available_playlists()
            if not playlists:
                print("❌ No playlist files found in data/playlists/")
                print("💡 Extract playlists first using the Anghami extractor")
                return
            
            print("\n📋 Available playlists:")
            for i, playlist_file in enumerate(playlists, 1):
                print(f"   {i}. {playlist_file.name}")
            
            print(f"   {len(playlists) + 1}. Migrate all playlists")
            
            while True:
                try:
                    choice = input(f"\nChoose playlist (1-{len(playlists) + 1}): ").strip()
                    
                    if choice == str(len(playlists) + 1):
                        # Migrate all
                        await migration_tool.migrate_multiple_playlists(
                            playlists,
                            skip_user_review=args.skip_review
                        )
                        break
                    else:
                        # Single playlist
                        playlist_index = int(choice) - 1
                        if 0 <= playlist_index < len(playlists):
                            await migration_tool.migrate_single_playlist(
                                playlists[playlist_index],
                                skip_user_review=args.skip_review
                            )
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(playlists) + 1}")
                
                except (ValueError, KeyboardInterrupt):
                    print("\n❌ Migration cancelled")
                    return
    
    # Run the migration
    asyncio.run(run_migration())


if __name__ == "__main__":
    main() 