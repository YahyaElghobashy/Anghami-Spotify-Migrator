#!/usr/bin/env python3
"""
Direct Anghami Playlist Extractor using Playwright
Extracts playlist metadata, tracks, cover art, and description directly from Anghami
"""

import asyncio
import json
import os
import re
import time
from urllib.parse import urlparse, parse_qs
from pathlib import Path
import requests
from playwright.async_api import async_playwright
import logging

# Import from new structure
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.models.anghami_models import AnghamiPlaylist, AnghamiTrack
from src.utils.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnghamiDirectExtractor:
    def __init__(self, config=None):
        self.config = config or get_config()
        
        # Use configured directories
        self.output_dir = self.config.directories.playlists_dir
        self.cover_art_dir = self.config.directories.cover_art_dir
        self.screenshots_dir = self.config.directories.screenshots_dir
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cover_art_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def extract_playlist(self, playlist_url: str) -> AnghamiPlaylist:
        """Extract complete playlist data directly from Anghami"""
        logger.info(f"Starting direct extraction for: {playlist_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config.extractor.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    f'--user-agent={self.config.extractor.user_agent}'
                ]
            )
            
            context = await browser.new_context(
                viewport={
                    'width': self.config.extractor.viewport_width, 
                    'height': self.config.extractor.viewport_height
                },
                user_agent=self.config.extractor.user_agent
            )
            
            page = await context.new_page()
            
            try:
                logger.info("Loading Anghami playlist page...")
                await page.goto(
                    playlist_url, 
                    wait_until='networkidle', 
                    timeout=self.config.extractor.page_load_timeout
                )
                await page.wait_for_timeout(self.config.extractor.default_wait_timeout)
                
                # Generate dynamic screenshot filename
                playlist_id = self._extract_playlist_id(playlist_url)
                screenshot_path = self.screenshots_dir / self.config.get_screenshot_filename(playlist_id)
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved as {screenshot_path}")
                
                playlist_data = await self._extract_playlist_metadata(page, playlist_url)
                tracks = await self._extract_tracks(page)
                playlist_data.tracks = tracks
                
                if playlist_data.cover_art_url:
                    cover_filename = await self._download_cover_art(playlist_data.cover_art_url, playlist_data.id)
                    if cover_filename:
                        playlist_data.cover_art_local_path = cover_filename
                
                # Use configured filename
                output_file = self.output_dir / self.config.get_playlist_filename(playlist_data.id, "direct")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(playlist_data.to_dict(), f, indent=2, ensure_ascii=False)
                
                logger.info(f"Playlist saved to {output_file}")
                logger.info(f"Extracted {len(tracks)} tracks from '{playlist_data.name}'")
                
                return playlist_data
                
            except Exception as e:
                logger.error(f"Error extracting playlist: {e}")
                # Save debug content with configured filename
                content = await page.content()
                debug_file = self.config.directories.temp_dir / self.config.extractor.debug_content_filename
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Debug content saved to {debug_file}")
                raise
            finally:
                await browser.close()
    
    async def _extract_playlist_metadata(self, page, url: str) -> AnghamiPlaylist:
        """Extract playlist metadata from the page"""
        playlist_id = self._extract_playlist_id(url)
        
        # Extract playlist name using configured selectors
        name_selectors = self.config.extractor.playlist_name_selectors
        
        playlist_name = "Unknown Playlist"
        for selector in name_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        playlist_name = await element.get_attribute('content') or ""
                else:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        name = await element.inner_text()
                        if name and name.strip():
                            playlist_name = name.strip()
                if playlist_name and playlist_name != "Unknown Playlist":
                    break
            except:
                continue
        
        # Extract description using configured selectors
        description_selectors = self.config.extractor.description_selectors
        
        description = ""
        for selector in description_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        description = await element.get_attribute('content') or ""
                else:
                    element = await page.query_selector(selector)
                    if element:
                        description = await element.inner_text() or ""
                        description = description.strip()
                if description:
                    break
            except:
                continue
        
        # Extract cover art URL using configured selectors
        cover_art_selectors = self.config.extractor.cover_art_selectors
        
        cover_art_url = ""
        for selector in cover_art_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        cover_art_url = await element.get_attribute('content') or ""
                else:
                    element = await page.query_selector(selector)
                    if element:
                        cover_art_url = await element.get_attribute('src') or ""
                if cover_art_url and cover_art_url.startswith('http'):
                    break
            except:
                continue
        
        # Extract creator info using configured selectors (playlist creator, not first song artist)
        creator_selectors = self.config.extractor.creator_selectors
        
        creator = ""
        for selector in creator_selectors:
            try:
                if selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        creator = await element.get_attribute('content') or ""
                else:
                    element = await page.query_selector(selector)
                    if element:
                        creator = await element.inner_text() or ""
                        creator = creator.strip()
                if creator:
                    break
            except:
                continue
        
        # Extract track count using configured selectors
        track_count = 0
        track_count_selectors = self.config.extractor.track_count_selectors
        
        for selector in track_count_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    count_text = await element.inner_text()
                    if count_text:
                        # Extract number from text like "128 Songs"
                        import re
                        numbers = re.findall(r'\d+', count_text)
                        if numbers:
                            track_count = int(numbers[0])
                            break
            except:
                continue
        
        logger.info(f"Extracted metadata - Name: '{playlist_name}', Creator: '{creator}', Description: '{description[:50]}...', Track count: {track_count}")
        
        return AnghamiPlaylist(
            id=playlist_id,
            name=playlist_name,
            url=url,
            description=description,
            creator_name=creator,
            tracks=[],
            track_count=track_count,
            cover_art_url=cover_art_url
        )
    
    async def _extract_tracks(self, page) -> list[AnghamiTrack]:
        """Extract all tracks from the playlist"""
        tracks = []
        
        # First, scroll to load all content
        await self._scroll_to_load_all_tracks(page)
        
        # Focus on Anghami's specific table-row structure for tracks
        logger.info("Extracting tracks from Anghami table structure...")
        
        try:
            # Wait for the track list to be fully loaded
            await page.wait_for_selector(
                self.config.extractor.track_row_selector, 
                timeout=self.config.extractor.element_wait_timeout
            )
            
            # Get all track row elements
            track_elements = await page.query_selector_all(self.config.extractor.track_row_selector)
            logger.info(f"Found {len(track_elements)} track row elements")
            
            for i, track_element in enumerate(track_elements):
                try:
                    # Extract song title using configured selector
                    title_element = await track_element.query_selector(self.config.extractor.track_title_selector)
                    song_title = ""
                    if title_element:
                        song_title = await title_element.inner_text()
                        song_title = song_title.strip() if song_title else ""
                    
                    # Extract artist using configured selector
                    artist_element = await track_element.query_selector(self.config.extractor.track_artist_selector)
                    artist_name = ""
                    if artist_element:
                        artist_name = await artist_element.inner_text()
                        artist_name = artist_name.strip() if artist_name else ""
                    
                    # Validate that we have both title and artist
                    if song_title and artist_name and len(song_title) > 1 and len(artist_name) > 1:
                        track = AnghamiTrack(
                            title=song_title,
                            artists=[artist_name]
                        )
                        tracks.append(track)
                        logger.debug(f"Track {i+1}: {song_title} - {artist_name}")
                    else:
                        logger.debug(f"Skipped invalid track at position {i+1}: title='{song_title}', artist='{artist_name}'")
                        
                except Exception as e:
                    logger.debug(f"Error extracting track {i+1}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(tracks)} tracks from DOM structure")
            
        except Exception as e:
            logger.error(f"Error in DOM-based track extraction: {e}")
        
        # Only fall back to text extraction if DOM extraction completely failed
        if not tracks:
            logger.warning("DOM extraction failed, falling back to text-based extraction")
            tracks = await self._extract_tracks_from_text_fallback(page)
        
        return tracks
    
    async def _scroll_to_load_all_tracks(self, page):
        """Scroll down to ensure all tracks are loaded using Anghami's lazy loading"""
        try:
            logger.info("Loading all tracks with enhanced scrolling...")
            
            # Get initial track count
            await page.wait_for_selector(
                self.config.extractor.track_row_selector, 
                timeout=self.config.extractor.element_wait_timeout
            )
            initial_tracks = await page.query_selector_all(self.config.extractor.track_row_selector)
            logger.info(f"Initial tracks loaded: {len(initial_tracks)}")
            
            previous_count = len(initial_tracks)
            stable_count = 0
            max_stable_iterations = self.config.extractor.stable_scroll_iterations
            
            # Scroll until no new tracks are loaded
            for scroll_iteration in range(self.config.extractor.max_scroll_attempts):
                # Scroll to bottom
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(self.config.extractor.scroll_wait_timeout)  # Wait for new content to load
                
                # Check for new tracks
                current_tracks = await page.query_selector_all(self.config.extractor.track_row_selector)
                current_count = len(current_tracks)
                
                logger.info(f"Scroll {scroll_iteration + 1}: {current_count} tracks loaded")
                
                if current_count > previous_count:
                    # New tracks loaded, reset stability counter
                    previous_count = current_count
                    stable_count = 0
                else:
                    # No new tracks, increment stability counter
                    stable_count += 1
                    
                    # If count has been stable for several iterations, we're done
                    if stable_count >= max_stable_iterations:
                        logger.info(f"Track count stable at {current_count} tracks")
                        break
                
                # Additional check: if we've reached the expected track count (126-130), stop
                if current_count >= 125:
                    logger.info(f"Reached expected track count: {current_count}")
                    break
                
                # Try scrolling inside the track container as well
                track_container = await page.query_selector('[class*="container-table100"]')
                if track_container:
                    await track_container.evaluate("element => element.scrollTop = element.scrollHeight")
                    await page.wait_for_timeout(1000)
            
            # Final count
            final_tracks = await page.query_selector_all(self.config.extractor.track_row_selector)
            logger.info(f"Final track count after scrolling: {len(final_tracks)}")
            
            # Scroll back to top to start fresh
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(self.config.extractor.scroll_wait_timeout)
            
        except Exception as e:
            logger.error(f"Error during enhanced scrolling: {e}")
            # Fallback: basic scrolling
            for _ in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)
    
    async def _extract_tracks_from_text_fallback(self, page) -> list[AnghamiTrack]:
        """Fallback: extract tracks by analyzing page text content (last resort)"""
        logger.info("Using fallback text-based track extraction...")
        tracks = []
        
        try:
            # Get visible text content only from the track list section
            track_section = await page.query_selector('[class*="container-table100"]')
            if track_section:
                content = await track_section.inner_text()
            else:
                content = await page.inner_text()
            
            # Split content into lines and look for track patterns
            lines = content.split('\n')
            current_title = ""
            current_artist = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip obvious UI elements and metadata
                if any(skip_word in line.lower() for skip_word in [
                    'play', 'download', 'like', 'more', 'playlist', 'songs', 'experimental',
                    'follow', 'share', 'add to', 'created by', 'description', 'cover',
                    'anghami', 'music', 'app', 'web', 'mobile', 'premium', 'free',
                    'sign up', 'log in', 'search', 'browse', 'discover', 'radio',
                    'class=', 'href=', 'src=', 'data-', 'http', 'www', '.com', '.png', '.jpg'
                ]):
                    continue
                
                # Look for artist names (usually shorter, often single words or two words)
                # and song titles (usually longer, more descriptive)
                if len(line) <= 30 and not any(char in line for char in ['=', '<', '>', '{', '}', '[', ']']):
                    if current_title and not current_artist:
                        current_artist = line
                        # Create track when we have both title and artist
                        if current_title and current_artist:
                            tracks.append(AnghamiTrack(
                                title=current_title,
                                artists=[current_artist]
                            ))
                            current_title = ""
                            current_artist = ""
                    elif not current_title:
                        current_title = line
            
            # Limit to reasonable number
            if len(tracks) > 150:
                tracks = tracks[:150]
            
            logger.info(f"Fallback text extraction found {len(tracks)} tracks")
            
        except Exception as e:
            logger.error(f"Error in fallback text extraction: {e}")
        
        return tracks
    
    def _extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from URL"""
        try:
            if '/playlist/' in url:
                return url.split('/playlist/')[-1].split('?')[0].split('/')[0]
            return str(int(time.time()))
        except:
            return str(int(time.time()))
    
    async def _download_cover_art(self, cover_url: str, playlist_id: str) -> str:
        """Download cover art image"""
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
                ext = 'webp'  # Default
            
            filename = self.config.get_cover_art_filename(playlist_id, ext)
            filepath = self.cover_art_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Cover art downloaded: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to download cover art: {e}")
            return ""

async def main():
    """Main function to test the extractor"""
    import sys
    
    extractor = AnghamiDirectExtractor()
    
    # Get URL from command line argument or prompt user
    if len(sys.argv) > 1:
        playlist_url = sys.argv[1]
    else:
        playlist_url = input("Enter Anghami playlist URL: ").strip()
        if not playlist_url:
            print("❌ No playlist URL provided")
            return
    
    try:
        playlist = await extractor.extract_playlist(playlist_url)
        print(f"\n✅ Direct Anghami extraction completed!")
        print(f"📀 Playlist: {playlist.name}")
        print(f"👤 Creator: {playlist.creator_name}")
        print(f"🎵 Tracks: {len(playlist.tracks)}")
        print(f"📝 Description: {playlist.description[:100]}..." if playlist.description else "📝 Description: None")
        print(f"🖼️  Cover art: {playlist.cover_art_local_path if hasattr(playlist, 'cover_art_local_path') else 'Not downloaded'}")
        
        # Print first few tracks
        if playlist.tracks:
            print(f"\n🎶 First 10 tracks:")
            for i, track in enumerate(playlist.tracks[:10]):
                print(f"  {i+1}. {track.title} - {track.primary_artist}")
        
        if len(playlist.tracks) > 10:
            print(f"  ... and {len(playlist.tracks) - 10} more tracks")
            
        print(f"\n📁 Data saved to: extracted_playlists/playlist_{playlist.id}_direct.json")
        
    except Exception as e:
        print(f"❌ Direct extraction failed: {e}")
        print("💡 Try the TuneMyMusic proxy extractor as an alternative.")

if __name__ == "__main__":
    asyncio.run(main()) 