#!/usr/bin/env python3
"""
Anghami Profile Data Extractor
Extracts profile information including name, avatar, follower count, and most played songs from Anghami profile pages
"""

import asyncio
import json
import logging
import re
from urllib.parse import urlparse
from pathlib import Path
from playwright.async_api import async_playwright

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnghamiProfileExtractor:
    def __init__(self):
        self.screenshots_dir = Path("data/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def extract_profile_data(self, profile_url: str) -> dict:
        """Extract complete profile data from Anghami profile page"""
        logger.info(f"Starting profile extraction for: {profile_url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--disable-gpu',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                ]
            )
            
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                logger.info("Loading Anghami profile page...")
                await page.goto(profile_url, wait_until='domcontentloaded', timeout=20000)
                await page.wait_for_timeout(2000)  # Reduced wait time
                
                # Take screenshot for debugging
                profile_id = self._extract_profile_id(profile_url)
                screenshot_path = self.screenshots_dir / f"profile_{profile_id}_loaded.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)
                logger.info(f"Screenshot saved as {screenshot_path}")
                
                # Extract profile data
                profile_data = await self._extract_profile_metadata(page, profile_url)
                
                logger.info(f"Successfully extracted profile data: {profile_data['display_name']}")
                return profile_data
                
            except Exception as e:
                logger.error(f"Error extracting profile: {e}")
                # Save debug content
                try:
                    content = await page.content()
                    debug_file = self.screenshots_dir / f"profile_{profile_id}_error_content.html"
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    logger.info(f"Debug content saved to {debug_file}")
                except:
                    logger.warning("Could not save debug content")
                raise
            finally:
                await browser.close()
    
    async def _extract_profile_metadata(self, page, profile_url: str) -> dict:
        """Extract profile metadata from the page"""
        profile_id = self._extract_profile_id(profile_url)
        
        # Extract display name
        display_name = await self._extract_display_name(page)
        
        # Extract avatar URL
        avatar_url = await self._extract_avatar_url(page)
        
        # Extract follower count
        follower_count = await self._extract_follower_count(page)
        
        # Extract most played songs (with More button click)
        most_played_songs = await self._extract_most_played_songs(page)
        
        return {
            "profile_url": profile_url,
            "profile_id": profile_id,
            "display_name": display_name,
            "avatar_url": avatar_url,
            "follower_count": follower_count,
            "most_played_songs": most_played_songs,
            "is_valid": True,
            "error_message": None
        }
    
    async def _extract_display_name(self, page) -> str:
        """Extract user's real display name from profile header"""
        logger.info("Extracting user display name...")
        
        # The user's name appears in the left sidebar profile section, not in the main content area
        # Look for the profile name in the sidebar or profile header area
        name_selectors = [
            # Try to get the name from the page title first (most reliable)
            'title',
            # Profile name in the left sidebar  
            '.profile-info h1',
            '.profile-header h1',
            '.user-info h1',
            '.sidebar h1',
            # Try various profile-related selectors
            '[class*="profile"] h1:not([class*="section"])',
            '[class*="user"] h1:not([class*="section"])',
            # Meta tags as fallback
            'meta[property="og:title"]',
            'meta[name="twitter:title"]'
        ]
        
        for selector in name_selectors:
            try:
                if selector == 'title':
                    title = await page.title()
                    if title:
                        # Extract name from title like "Yahya Elghobashy | Anghami" or "Yara Aboubakr | Anghami"
                        if ' | Anghami' in title:
                            name = title.split(' | Anghami')[0].strip()
                        elif ' - Anghami' in title:
                            name = title.split(' - Anghami')[0].strip()
                        else:
                            name = title.strip()
                        
                        # Make sure it's not a generic title
                        if name and not name.lower() in ['anghami', 'most played songs', 'followed artists']:
                            logger.info(f"Extracted name from title: {name}")
                            return name
                            
                elif selector.startswith('meta'):
                    element = await page.query_selector(selector)
                    if element:
                        content = await element.get_attribute('content')
                        if content and ' | Anghami' in content:
                            name = content.split(' | Anghami')[0].strip()
                            if name and not name.lower() in ['anghami', 'most played songs', 'followed artists']:
                                logger.info(f"Extracted name from meta: {name}")
                                return name
                else:
                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        if element:
                            text = await element.inner_text()
                            if text and text.strip():
                                cleaned_text = text.strip()
                                # Skip section titles and generic content
                                if not any(skip in cleaned_text.lower() for skip in 
                                         ['most played', 'followed artists', 'recently played', 'playlists', 'albums']):
                                    logger.info(f"Extracted name from element: {cleaned_text}")
                                    return cleaned_text
                                    
            except Exception as e:
                logger.debug(f"Error with name selector {selector}: {e}")
                continue
        
        logger.warning("Could not extract display name, using fallback")
        return "Anghami User"
    
    async def _extract_avatar_url(self, page) -> str:
        """Extract user's avatar/profile picture URL"""
        logger.info("Extracting avatar URL...")
        
        # Anghami-specific avatar selectors
        avatar_selectors = [
            'img.shadow-borders',  # The specific class from the HTML
            'img[src*="artwork.anghcdn.co/user/"]',  # Anghami user CDN images
            # Fallback selectors
            'img[class*="profile"]',
            'img[class*="avatar"]', 
            'img[class*="user"]'
        ]
        
        for selector in avatar_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    src = await element.get_attribute('src')
                    if src and src.startswith('http'):
                        logger.info(f"Found avatar URL: {src}")
                        return src
            except Exception as e:
                logger.debug(f"Error with avatar selector {selector}: {e}")
                continue
        
        logger.warning("Could not find avatar URL")
        return None
    
    async def _extract_follower_count(self, page) -> int:
        """Extract follower count from profile stats"""
        logger.info("Extracting follower count...")
        
        try:
            # Look for the followers section in the profile stats
            stats_section = await page.query_selector('.section-details')
            if stats_section:
                # Get all text from the stats section
                stats_text = await stats_section.inner_text()
                logger.debug(f"Stats section text: {stats_text}")
                
                # Look for follower patterns like "1.3K Followers" or "18 Followers"
                follower_patterns = [
                    r'([\d.]+[km]?)\s*followers',
                    r'([\d.]+[km]?)\s*متابع',  # Arabic
                    r'followers\s*([\d.]+[km]?)',
                    r'متابع\s*([\d.]+[km]?)'  # Arabic
                ]
                
                for pattern in follower_patterns:
                    matches = re.findall(pattern, stats_text.lower(), re.IGNORECASE)
                    if matches:
                        number_str = matches[0]
                        count = self._parse_follower_number(number_str)
                        logger.info(f"Extracted follower count: {count}")
                        return count
            
            # Fallback: search entire page content
            page_content = await page.content()
            follower_patterns = [
                r'(\d+(?:\.\d+)?[km]?)\s*followers',
                r'followers.*?(\d+(?:\.\d+)?[km]?)',
            ]
            
            for pattern in follower_patterns:
                matches = re.findall(pattern, page_content.lower(), re.IGNORECASE)
                if matches:
                    for match in matches:
                        count = self._parse_follower_number(match)
                        if count > 0:
                            logger.info(f"Extracted follower count from content: {count}")
                            return count
                            
        except Exception as e:
            logger.error(f"Error extracting follower count: {e}")
        
        logger.warning("Could not extract follower count")
        return 0
    
    def _parse_follower_number(self, number_str: str) -> int:
        """Parse follower number from strings like '1.3K', '2.5M', '18' etc."""
        try:
            number_str = number_str.strip().lower()
            
            if number_str.endswith('k'):
                base_number = float(number_str[:-1])
                return int(base_number * 1000)
            elif number_str.endswith('m'):
                base_number = float(number_str[:-1])
                return int(base_number * 1000000)
            else:
                return int(float(number_str))
        except:
            return 0
    
    async def _extract_most_played_songs(self, page) -> list:
        """Extract most played songs, clicking More button to load additional songs"""
        songs = []
        logger.info("Extracting most played songs...")
        
        try:
            # Wait for the songs section to load initially  
            await page.wait_for_selector('.table-row', timeout=8000)
            await page.wait_for_timeout(500)  # Let content stabilize
            
            # Take screenshot before More click for debugging
            current_url = page.url
            profile_id = self._extract_profile_id(current_url)
            screenshot_before = self.screenshots_dir / f"profile_{profile_id}_before_more.png"
            await page.screenshot(path=str(screenshot_before), full_page=True)
            logger.info(f"Screenshot before More click saved as {screenshot_before}")
            
            # Count initial songs
            initial_song_rows = await page.query_selector_all('.table-row')
            initial_count = len(initial_song_rows)
            logger.info(f"Initial song count: {initial_count}")
            
            # Try to click the "More" button to load additional songs
            more_clicked = False
            try:
                # Look for the More button specifically
                more_button = await page.query_selector('button.anghami-default-btn')
                if more_button:
                    button_text = await more_button.inner_text()
                    logger.info(f"Found button with text: '{button_text}'")
                    
                    if 'more' in button_text.lower():
                        logger.info("Clicking 'More' button to load additional songs...")
                        await more_button.click()
                        more_clicked = True
                        
                        # Wait for new content to load - look for increased row count
                        max_wait_attempts = 6
                        for attempt in range(max_wait_attempts):
                            await page.wait_for_timeout(300)
                            current_rows = await page.query_selector_all('.table-row')
                            current_count = len(current_rows)
                            logger.debug(f"Attempt {attempt + 1}: {current_count} rows (was {initial_count})")
                            
                            if current_count > initial_count:
                                logger.info(f"More content loaded: {current_count} rows (was {initial_count})")
                                break
                        
                        # Wait a bit more for content to stabilize
                        await page.wait_for_timeout(800)
                        
                        # Take screenshot after More click for debugging
                        screenshot_after = self.screenshots_dir / f"profile_{profile_id}_after_more.png"
                        await page.screenshot(path=str(screenshot_after), full_page=True)
                        logger.info(f"Screenshot after More click saved as {screenshot_after}")
                        
                else:
                    logger.info("No More button found")
                    
            except Exception as e:
                logger.debug(f"Could not click More button: {e}")
            
            # Now extract songs from the table (get fresh list of rows)
            await page.wait_for_timeout(500)  # Brief stabilization
            song_rows = await page.query_selector_all('.table-row')
            total_rows = len(song_rows)
            logger.info(f"Found {total_rows} song rows after More button {'clicked' if more_clicked else 'not clicked'}")
            
            # Extract up to 10 songs, but ensure we get them in the correct order
            max_songs = min(10, total_rows)
            
            for i in range(max_songs):
                try:
                    # Get the row element fresh each time to avoid stale references
                    current_rows = await page.query_selector_all('.table-row')
                    if i >= len(current_rows):
                        logger.warning(f"Row {i} no longer exists, stopping extraction")
                        break
                        
                    row = current_rows[i]
                    
                    # Extract song title - look for the cell with song title
                    title_cell = await row.query_selector('.cell-title')
                    title = "Unknown Title"
                    if title_cell:
                        # Try multiple approaches to get the title
                        title_span = await title_cell.query_selector('span')
                        if title_span:
                            title = await title_span.inner_text()
                        else:
                            # Fallback: get text directly from cell
                            title = await title_cell.inner_text()
                        title = title.strip()
                    
                    # Extract artist name
                    artist_cell = await row.query_selector('.cell-artist')
                    artist = "Unknown Artist"
                    if artist_cell:
                        # Try link first, then direct text
                        artist_link = await artist_cell.query_selector('a')
                        if artist_link:
                            artist = await artist_link.inner_text()
                        else:
                            artist = await artist_cell.inner_text()
                        artist = artist.strip()
                    
                    # Extract album name  
                    album_cell = await row.query_selector('.cell-album')
                    album = None
                    if album_cell:
                        album_link = await album_cell.query_selector('a')
                        if album_link:
                            album = await album_link.inner_text()
                            album = album.strip() if album else None
                        else:
                            # Try getting text directly
                            album_text = await album_cell.inner_text()
                            if album_text and album_text.strip():
                                album = album_text.strip()
                    
                    # Extract cover art URL from background-image style
                    cover_url = None
                    cover_element = await row.query_selector('.list-item-image')
                    if cover_element:
                        style = await cover_element.get_attribute('style')
                        if style and 'background-image: url(' in style:
                            url_match = re.search(r'url\("?([^")]+)"?\)', style)
                            if url_match:
                                cover_url = url_match.group(1)
                    
                    # Validate the extracted data
                    if title != "Unknown Title" and artist != "Unknown Artist" and title.strip() and artist.strip():
                        song = {
                            "rank": i + 1,
                            "title": title,
                            "artist": artist,
                            "album": album,
                            "cover_url": cover_url
                        }
                        
                        songs.append(song)
                        logger.info(f"✓ Song {i+1}: '{title}' - '{artist}'" + (f" (Album: {album})" if album else ""))
                    else:
                        logger.warning(f"✗ Song {i+1}: Invalid data - Title: '{title}', Artist: '{artist}'")
                    
                except Exception as e:
                    logger.error(f"Error extracting song {i+1}: {e}")
                    # Try to continue with next song
                    continue
            
            logger.info(f"Successfully extracted {len(songs)} most played songs")
            
            # Log the final extracted songs for verification
            if songs:
                logger.info("Final song list:")
                for song in songs:
                    logger.info(f"  {song['rank']}. {song['title']} - {song['artist']}")
            
        except Exception as e:
            logger.error(f"Error extracting most played songs: {e}")
        
        return songs
    
    def _extract_profile_id(self, url: str) -> str:
        """Extract profile ID from URL"""
        try:
            parsed = urlparse(url)
            if '/profile/' in parsed.path:
                profile_id = parsed.path.split('/profile/')[-1].split('?')[0].split('/')[0]
                return profile_id
        except:
            pass
        return "unknown"

async def main():
    """Test the profile extractor with multiple profiles"""
    import sys
    
    extractor = AnghamiProfileExtractor()
    
    # Test profiles
    test_profiles = [
        "https://play.anghami.com/profile/3186485",  # Yahya Elghobashy
        "https://play.anghami.com/profile/16055208"   # Yara Aboubakr
    ]
    
    # Use provided URL or test both profiles
    if len(sys.argv) > 1:
        test_profiles = [sys.argv[1]]
    
    for profile_url in test_profiles:
        try:
            print(f"\n{'='*60}")
            print(f"Testing profile: {profile_url}")
            print(f"{'='*60}")
            
            profile_data = await extractor.extract_profile_data(profile_url)
            
            print(f"\n✅ Profile extraction completed!")
            print(f"📱 Profile URL: {profile_data['profile_url']}")
            print(f"👤 Display Name: {profile_data['display_name']}")
            print(f"🖼️  Avatar URL: {profile_data['avatar_url']}")
            print(f"👥 Followers: {profile_data['follower_count']:,}")
            print(f"🆔 Profile ID: {profile_data['profile_id']}")
            
            if profile_data['most_played_songs']:
                print(f"\n🎵 Most Played Songs ({len(profile_data['most_played_songs'])}):")
                for song in profile_data['most_played_songs']:
                    print(f"  {song['rank']}. {song['title']} - {song['artist']}")
                    if song['album']:
                        print(f"      Album: {song['album']}")
            else:
                print("\n🎵 No songs found")
                
        except Exception as e:
            print(f"❌ Profile extraction failed for {profile_url}: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 