#!/usr/bin/env python3
"""
TuneMyMusic Proxy Extractor for Anghami Playlists
Uses TuneMyMusic.com as an intermediary to extract Anghami playlist data
"""

import asyncio
import json
import time
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

class TuneMyMusicExtractor:
    def __init__(self, config=None):
        self.config = config or get_config()
        
        # Use configured directories
        self.output_dir = self.config.directories.playlists_dir
        self.screenshots_dir = self.config.directories.screenshots_dir
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def extract_playlist(self, playlist_url: str) -> AnghamiPlaylist:
        """Extract playlist data using TuneMyMusic as proxy"""
        logger.info(f"Starting TuneMyMusic proxy extraction for: {playlist_url}")
        
        async with async_playwright() as p:
            # Launch browser with configured settings
            browser = await p.chromium.launch(
                headless=self.config.extractor.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
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
            
            # Remove webdriver detection
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)
            
            page = await context.new_page()
            
            try:
                # Navigate to TuneMyMusic
                logger.info("Loading TuneMyMusic transfer page...")
                await page.goto(
                    self.config.tunemymusic.transfer_url, 
                    wait_until='networkidle', 
                    timeout=self.config.tunemymusic.navigation_timeout
                )
                await page.wait_for_timeout(self.config.extractor.default_wait_timeout)
                
                # Take screenshot of initial page
                initial_screenshot = self.screenshots_dir / "tunemymusic_initial.png"
                await page.screenshot(path=str(initial_screenshot))
                logger.info(f"Initial TuneMyMusic page screenshot saved: {initial_screenshot}")
                
                # Step 1: Select Anghami as source
                await self._select_anghami_source(page)
                
                # Step 2: Input the playlist URL
                await self._input_playlist_url(page, playlist_url)
                
                # Step 3: Click load and wait for results
                await self._load_playlist_data(page)
                
                # Step 4: Extract the playlist data
                playlist_data = await self._extract_playlist_from_tunemymusic(page, playlist_url)
                
                # Step 5: Save the data
                output_file = self.output_dir / self.config.get_playlist_filename(playlist_data.id, "tunemymusic")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(playlist_data.to_dict(), f, indent=2, ensure_ascii=False)
                
                logger.info(f"Playlist saved to {output_file}")
                logger.info(f"Extracted {len(playlist_data.tracks)} tracks via TuneMyMusic")
                
                return playlist_data
                
            except Exception as e:
                logger.error(f"Error in TuneMyMusic extraction: {e}")
                # Save debug screenshots and content
                error_screenshot = self.screenshots_dir / "tunemymusic_error.png"
                await page.screenshot(path=str(error_screenshot))
                
                content = await page.content()
                debug_file = self.config.directories.temp_dir / "tunemymusic_error_content.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Debug content saved to {debug_file}")
                raise
            finally:
                await browser.close()
    
    async def _select_anghami_source(self, page):
        """Select Anghami as the source platform"""
        logger.info("Selecting Anghami as source...")
        
        # Wait for the page to fully load
        await page.wait_for_timeout(3000)
        
        # Try multiple strategies to find and click the Anghami button
        anghami_selectors = [
            'button[aria-label="Anghami"]',
            'button[title="Anghami"]', 
            'button[name="Anghami"]',
            'button:has-text("Anghami")',
            '[class*="MusicServiceBlock"]:has-text("Anghami")',
            'button:has(img[alt="Anghami"])',
            'button:has(img[src*="Anghami"])'
        ]
        
        for selector in anghami_selectors:
            try:
                logger.info(f"Trying selector: {selector}")
                anghami_button = await page.wait_for_selector(selector, timeout=5000)
                if anghami_button:
                    await anghami_button.click()
                    logger.info("Anghami source selected successfully")
                    await page.wait_for_timeout(2000)
                    return
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # If specific selectors fail, try a more general approach
        try:
            # Look for any button containing "Anghami" text
            await page.click("text=Anghami")
            logger.info("Anghami selected using text selector")
            await page.wait_for_timeout(2000)
        except Exception as e:
            logger.error(f"Failed to select Anghami source: {e}")
            raise Exception("Could not find Anghami source button")
    
    async def _input_playlist_url(self, page, playlist_url: str):
        """Input the Anghami playlist URL"""
        logger.info(f"Inputting playlist URL: {playlist_url}")
        
        # Try multiple selectors for the URL input field
        input_selectors = [
            'input[placeholder*="Anghami playlist URL"]',
            'input[placeholder*="playlist URL"]',
            'input[placeholder*="URL"]',
            'input[id*="r0"]',
            'input[class*="input_input"]',
            'input[type="text"]'
        ]
        
        for selector in input_selectors:
            try:
                input_field = await page.wait_for_selector(selector, timeout=5000)
                if input_field:
                    # Clear any existing content and input the URL
                    await input_field.click()
                    await input_field.fill("")
                    await input_field.type(playlist_url)
                    logger.info("Playlist URL entered successfully")
                    await page.wait_for_timeout(1000)
                    return
            except Exception as e:
                logger.debug(f"Input selector {selector} failed: {e}")
                continue
        
        raise Exception("Could not find URL input field")
    
    async def _load_playlist_data(self, page):
        """Click the load button and wait for playlist data to load"""
        logger.info("Loading playlist data...")
        
        # Try to find and click the load button
        load_selectors = [
            'button:has-text("Load")',
            'button:has-text("load")',
            'button[type="submit"]',
            'input[type="submit"]',
            '[class*="load"]:visible',
            '[class*="Load"]:visible'
        ]
        
        for selector in load_selectors:
            try:
                load_button = await page.wait_for_selector(selector, timeout=5000)
                if load_button:
                    await load_button.click()
                    logger.info("Load button clicked")
                    break
            except Exception as e:
                logger.debug(f"Load selector {selector} failed: {e}")
                continue
        
        # Wait for the playlist to load - this might take a while
        logger.info("Waiting for playlist data to load...")
        await page.wait_for_timeout(10000)  # Wait 10 seconds initially
        
        # Look for signs that the playlist has loaded
        loading_indicators = [
            '[class*="PlayListRow_container"]',
            '[class*="playlist"]',
            '[class*="track"]',
            'div:has-text("selected")'
        ]
        
        # Wait up to 30 seconds for content to appear
        for _ in range(6):  # 6 * 5 seconds = 30 seconds max
            for indicator in loading_indicators:
                try:
                    element = await page.query_selector(indicator)
                    if element:
                        logger.info(f"Playlist content detected with selector: {indicator}")
                        await page.wait_for_timeout(3000)  # Give it a bit more time to fully load
                        return
                except:
                    continue
            
            logger.info("Still waiting for playlist content...")
            await page.wait_for_timeout(5000)
        
        logger.warning("Playlist content may not have loaded completely, proceeding anyway")
    
    async def _extract_playlist_from_tunemymusic(self, page, original_url: str) -> AnghamiPlaylist:
        """Extract playlist data from the TuneMyMusic interface"""
        logger.info("Extracting playlist data from TuneMyMusic interface...")
        
        # Take a screenshot of the loaded content
        loaded_screenshot = self.screenshots_dir / "tunemymusic_loaded.png"
        await page.screenshot(path=str(loaded_screenshot), full_page=True)
        logger.info(f"Screenshot of loaded content saved: {loaded_screenshot}")
        
        # Extract playlist metadata first
        playlist_metadata = await self._extract_playlist_metadata_from_tunemymusic(page, original_url)
        
        # Extract tracks using the specific HTML structure provided
        tracks = await self._extract_tracks_from_tunemymusic(page)
        
        playlist_metadata.tracks = tracks
        playlist_metadata.track_count = len(tracks)
        
        return playlist_metadata
    
    async def _extract_playlist_metadata_from_tunemymusic(self, page, original_url: str) -> AnghamiPlaylist:
        """Extract playlist metadata from TuneMyMusic"""
        # Extract playlist name from the main container
        playlist_name = "Unknown Playlist"
        
        # Look for playlist name in the PlayListRow_container
        name_selectors = [
            '[class*="PlayListRow_playListName"]',
            '[class*="playListName"]',
            '[class*="playlist-name"]',
            '.PlayListRow_playListName___QMiP'
        ]
        
        for selector in name_selectors:
            try:
                name_element = await page.query_selector(selector)
                if name_element:
                    name_text = await name_element.inner_text()
                    if name_text and name_text.strip():
                        playlist_name = name_text.strip()
                        break
            except:
                continue
        
        # Extract cover art URL
        cover_art_url = ""
        cover_selectors = [
            '.PlayListRow_ResourceImage__Vz0SU',
            '[class*="ResourceImage"]',
            '[class*="PlayListRow"] img[src*="anghami"]'
        ]
        
        for selector in cover_selectors:
            try:
                img_element = await page.query_selector(selector)
                if img_element:
                    src = await img_element.get_attribute('src')
                    if src and src.startswith('http'):
                        cover_art_url = src
                        break
            except:
                continue
        
        # Generate playlist ID from original URL
        playlist_id = self._extract_playlist_id(original_url)
        
        logger.info(f"Extracted playlist metadata - Name: {playlist_name}")
        
        return AnghamiPlaylist(
            id=playlist_id,
            name=playlist_name,
            url=original_url,
            description="",
            creator_name="",  # Will try to extract later
            tracks=[],  # Will be filled
            track_count=0,  # Will be updated
            cover_art_url=cover_art_url
        )
    
    async def _extract_tracks_from_tunemymusic(self, page) -> list[AnghamiTrack]:
        """Extract tracks using the specific TuneMyMusic HTML structure"""
        tracks = []
        
        # Look for the tracks table/container
        track_containers = [
            '.PlayListRow_songsTable__6BdOH',
            '[class*="songsTable"]',
            '[class*="PlayListRow_container"] [class*="subRow"]'
        ]
        
        # Find the main tracks container
        tracks_container = None
        for container_selector in track_containers:
            try:
                container = await page.query_selector(container_selector)
                if container:
                    tracks_container = container
                    logger.info(f"Found tracks container with selector: {container_selector}")
                    break
            except:
                continue
        
        if not tracks_container:
            logger.warning("Could not find tracks container, trying alternative approach")
            return await self._extract_tracks_alternative_approach(page)
        
        # Extract individual track rows based on the provided HTML structure
        track_row_selector = '.PlayListRow_subRow__dTPmX'
        
        try:
            track_rows = await tracks_container.query_selector_all(track_row_selector)
            logger.info(f"Found {len(track_rows)} track rows")
            
            for i, row in enumerate(track_rows):
                track = await self._extract_track_from_tunemymusic_row(row, i + 1)
                if track:
                    tracks.append(track)
            
        except Exception as e:
            logger.error(f"Error extracting tracks from rows: {e}")
            # Fallback to alternative method
            return await self._extract_tracks_alternative_approach(page)
        
        logger.info(f"Successfully extracted {len(tracks)} tracks from TuneMyMusic")
        return tracks
    
    async def _extract_track_from_tunemymusic_row(self, row_element, position: int) -> AnghamiTrack:
        """Extract track info from a single TuneMyMusic row element"""
        try:
            # Extract song name using the specific class from the HTML structure
            song_name_element = await row_element.query_selector('.PlayListRow_innerName__ErNgP')
            song_name = ""
            if song_name_element:
                song_name = await song_name_element.inner_text()
            
            # Extract artist name using the specific class from the HTML structure  
            artist_name_element = await row_element.query_selector('.PlayListRow_innerArtist__GPUeU')
            artist_name = ""
            if artist_name_element:
                artist_name = await artist_name_element.inner_text()
            
            if song_name and artist_name:
                return AnghamiTrack(
                    title=song_name.strip(),
                    artists=[artist_name.strip()]
                )
            
        except Exception as e:
            logger.debug(f"Error extracting track from row: {e}")
        
        return None
    
    async def _extract_tracks_alternative_approach(self, page) -> list[AnghamiTrack]:
        """Alternative approach to extract tracks if main method fails"""
        logger.info("Using alternative track extraction approach...")
        tracks = []
        
        try:
            # Get all text content and look for track patterns
            content = await page.content()
            
            # Save content for debugging
            with open('tunemymusic_content_debug.html', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Look for the specific class patterns in the content
            import re
            
            # Pattern to match the track structure from the provided HTML
            track_pattern = r'PlayListRow_innerName__ErNgP[^>]*>([^<]+)<.*?PlayListRow_innerArtist__GPUeU[^>]*>([^<]+)<'
            
            matches = re.findall(track_pattern, content, re.DOTALL)
            
            for i, (song_name, artist_name) in enumerate(matches):
                # Clean up the extracted text
                song_name = song_name.strip()
                artist_name = artist_name.strip()
                
                if song_name and artist_name:
                    tracks.append(AnghamiTrack(
                        title=song_name,
                        artists=[artist_name]
                    ))
            
            logger.info(f"Alternative extraction found {len(tracks)} tracks")
            
        except Exception as e:
            logger.error(f"Alternative extraction failed: {e}")
        
        return tracks
    
    def _extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from original Anghami URL"""
        try:
            if '/playlist/' in url:
                return url.split('/playlist/')[-1].split('?')[0].split('/')[0]
            return str(int(time.time()))
        except:
            return str(int(time.time()))

async def main():
    """Main function to test the TuneMyMusic extractor"""
    import sys
    
    extractor = TuneMyMusicExtractor()
    
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
        print(f"\nTuneMyMusic extraction completed!")
        print(f"Playlist: {playlist.name}")
        print(f"Tracks: {len(playlist.tracks)}")
        print(f"Cover art URL: {playlist.cover_art_url}")
        
        # Print first 10 tracks
        for i, track in enumerate(playlist.tracks[:10]):
            print(f"{i+1}. {track.title} - {track.primary_artist}")
        
        if len(playlist.tracks) > 10:
            print(f"... and {len(playlist.tracks) - 10} more tracks")
            
    except Exception as e:
        print(f"TuneMyMusic extraction failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 