#!/usr/bin/env python3
"""
TuneMyMusic Automation Script for Anghami to Spotify Migration

Automates the complete transfer workflow using TuneMyMusic.com:
1. Batch process multiple playlists
2. Avoid duplicate transfers  
3. Handle complete transfer workflow
4. Save unmigrated tracks as CSV
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
from playwright.async_api import async_playwright
import logging

# Import from new structure
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.utils.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TuneMyMusicAutomation:
    """Automated Anghami to Spotify playlist migration using TuneMyMusic"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        
        # Setup directories
        self.output_dir = self.config.directories.playlists_dir
        self.screenshots_dir = self.config.directories.screenshots_dir
        self.logs_dir = self.config.directories.logs_dir
        self.csv_dir = self.config.directories.data_dir / "unmigrated_tracks"
        
        # Create directories
        for directory in [self.output_dir, self.screenshots_dir, self.logs_dir, self.csv_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Track processed playlists
        self.processed_file = self.logs_dir / "processed_playlists.json"
        self.processed_playlists = self._load_processed_playlists()
        
        # Migration session tracking
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_log = self.logs_dir / f"migration_session_{self.session_id}.log"
        
        # Statistics
        self.stats = {
            "total_playlists": 0,
            "successful_transfers": 0,
            "failed_transfers": 0,
            "skipped_duplicates": 0,
            "total_tracks_migrated": 0,
            "total_tracks_unmigrated": 0,
            "start_time": None,
            "end_time": None
        }

    def _load_processed_playlists(self) -> Set[str]:
        """Load list of already processed playlists to avoid duplicates"""
        try:
            if self.processed_file.exists():
                with open(self.processed_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('processed_urls', []))
        except Exception as e:
            logger.warning(f"Could not load processed playlists: {e}")
        return set()

    def _save_processed_playlists(self):
        """Save the list of processed playlists"""
        try:
            data = {
                "processed_urls": list(self.processed_playlists),
                "last_updated": datetime.now().isoformat(),
                "total_processed": len(self.processed_playlists)
            }
            with open(self.processed_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save processed playlists: {e}")

    def _log_session(self, message: str):
        """Log to session file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.session_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def _extract_playlist_id(self, url: str) -> str:
        """Extract playlist ID from URL"""
        try:
            if '/playlist/' in url:
                return url.split('/playlist/')[-1].split('?')[0].split('/')[0]
            return str(int(time.time()))
        except:
            return str(int(time.time()))

    async def migrate_playlists(self, playlist_urls: List[str]) -> Dict:
        """Migrate multiple playlists using TuneMyMusic automation"""
        logger.info(f"🚀 Starting batch migration of {len(playlist_urls)} playlists")
        self.stats["total_playlists"] = len(playlist_urls)
        self.stats["start_time"] = datetime.now()
        self._log_session(f"Started migration session with {len(playlist_urls)} playlists")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.config.extractor.headless,
                args=[
                    '--no-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
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
                for i, playlist_url in enumerate(playlist_urls, 1):
                    logger.info(f"\n📀 Processing playlist {i}/{len(playlist_urls)}: {playlist_url}")
                    
                    # Check if already processed
                    if playlist_url in self.processed_playlists:
                        logger.info("⏭️  Playlist already processed, skipping...")
                        self.stats["skipped_duplicates"] += 1
                        continue
                    
                    try:
                        # Perform the complete migration for this playlist
                        result = await self._migrate_single_playlist(page, playlist_url, i)
                        
                        if result["success"]:
                            self.stats["successful_transfers"] += 1
                            self.stats["total_tracks_migrated"] += result.get("tracks_migrated", 0)
                            self.stats["total_tracks_unmigrated"] += result.get("tracks_unmigrated", 0)
                            self.processed_playlists.add(playlist_url)
                            logger.info(f"✅ Successfully migrated playlist {i}")
                        else:
                            self.stats["failed_transfers"] += 1
                            logger.error(f"❌ Failed to migrate playlist {i}: {result.get('error', 'Unknown error')}")
                        
                        # Save progress after each playlist
                        self._save_processed_playlists()
                        
                        # Wait between playlists to avoid rate limiting
                        if i < len(playlist_urls):
                            logger.info("⏸️  Waiting 30 seconds before next playlist...")
                            await asyncio.sleep(30)
                            
                    except Exception as e:
                        logger.error(f"❌ Error processing playlist {i}: {e}")
                        self.stats["failed_transfers"] += 1
                        self._log_session(f"Failed playlist {i}: {e}")
                        continue
                
            finally:
                await browser.close()
                self.stats["end_time"] = datetime.now()
                await self._generate_final_report()
        
        return self.stats

    async def _migrate_single_playlist(self, page, playlist_url: str, playlist_number: int) -> Dict:
        """Migrate a single playlist through the complete TuneMyMusic workflow"""
        playlist_id = self._extract_playlist_id(playlist_url)
        
        try:
            # Step 1: Navigate to TuneMyMusic
            logger.info("🌐 Loading TuneMyMusic...")
            await page.goto(
                self.config.tunemymusic.transfer_url,
                wait_until='networkidle',
                timeout=self.config.tunemymusic.navigation_timeout
            )
            await page.wait_for_timeout(3000)
            
            # Step 2: Select Anghami as source
            logger.info("🎵 Selecting Anghami as source...")
            await self._select_anghami_source(page)
            
            # Step 3: Input playlist URL
            logger.info("🔗 Entering playlist URL...")
            await self._input_playlist_url(page, playlist_url)
            
            # Step 4: Load playlist
            logger.info("📥 Loading playlist data...")
            await self._load_playlist_data(page)
            
            # Take screenshot of loaded playlist
            loaded_screenshot = self.screenshots_dir / f"playlist_{playlist_id}_loaded.png"
            await page.screenshot(path=str(loaded_screenshot))
            
            # Step 5: Select Spotify as destination
            logger.info("🎯 Selecting Spotify as destination...")
            await self._select_spotify_destination(page)
            
            # Step 6: Configure transfer settings
            logger.info("⚙️ Configuring transfer settings...")
            await self._configure_transfer_settings(page)
            
            # Step 7: Start the transfer
            logger.info("🚀 Starting transfer to Spotify...")
            transfer_result = await self._start_transfer(page)
            
            # Step 8: Wait for completion and get results
            logger.info("⏳ Waiting for transfer completion...")
            completion_result = await self._wait_for_completion(page)
            
            # Step 9: Download unmigrated tracks CSV if available
            logger.info("📄 Checking for unmigrated tracks...")
            csv_result = await self._download_unmigrated_csv(page, playlist_id)
            
            # Step 10: Take final screenshot
            final_screenshot = self.screenshots_dir / f"playlist_{playlist_id}_completed.png"
            await page.screenshot(path=str(final_screenshot))
            
            result = {
                "success": True,
                "playlist_id": playlist_id,
                "tracks_migrated": completion_result.get("tracks_migrated", 0),
                "tracks_unmigrated": completion_result.get("tracks_unmigrated", 0),
                "spotify_playlist_url": completion_result.get("spotify_url", ""),
                "csv_file": csv_result.get("csv_file", ""),
                "screenshots": [str(loaded_screenshot), str(final_screenshot)]
            }
            
            self._log_session(f"Successfully migrated playlist {playlist_number}: {playlist_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error in single playlist migration: {e}")
            
            # Take error screenshot
            error_screenshot = self.screenshots_dir / f"playlist_{playlist_id}_error.png"
            await page.screenshot(path=str(error_screenshot))
            
            return {
                "success": False,
                "playlist_id": playlist_id,
                "error": str(e),
                "screenshot": str(error_screenshot)
            }

    async def _select_anghami_source(self, page):
        """Select Anghami as the source platform"""
        anghami_selectors = [
            self.config.tunemymusic.anghami_button_selector,
            'button[data-id="3"]',  # Anghami's data-id
            'button[aria-label="Anghami"]',
            'button:has-text("Anghami")',
            '[class*="MusicServiceBlock"]:has-text("Anghami")',
            'button:has(img[alt*="Anghami"])'
        ]
        
        for selector in anghami_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.click()
                    await page.wait_for_timeout(2000)
                    logger.info("✅ Anghami source selected")
                    return
            except:
                continue
        
        raise Exception("Could not find Anghami source button")

    async def _input_playlist_url(self, page, playlist_url: str):
        """Input the Anghami playlist URL"""
        input_selectors = [
            self.config.tunemymusic.url_input_selector,
            'input[placeholder*="playlist"]',
            'input[placeholder*="URL"]',
            'input[type="text"]:visible'
        ]
        
        for selector in input_selectors:
            try:
                input_field = await page.wait_for_selector(selector, timeout=5000)
                if input_field:
                    await input_field.click()
                    await input_field.fill("")
                    await input_field.type(playlist_url)
                    await page.wait_for_timeout(1000)
                    logger.info("✅ Playlist URL entered")
                    return
            except:
                continue
        
        raise Exception("Could not find URL input field")

    async def _load_playlist_data(self, page):
        """Load the playlist data"""
        load_selectors = [
            self.config.tunemymusic.load_button_selector,
            'button:has-text("Load my music")',
            'button:has-text("Load")',
            'button[type="submit"]'
        ]
        
        for selector in load_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button:
                    await button.click()
                    break
            except:
                continue
        
        # Wait for playlist to load
        await page.wait_for_timeout(15000)
        
        # Wait for tracks to appear
        for _ in range(12):  # Wait up to 60 seconds
            try:
                tracks = await page.query_selector_all('.PlayListRow_row__1n_NK')
                if len(tracks) > 0:
                    logger.info(f"✅ Playlist loaded with {len(tracks)} tracks")
                    return
            except:
                pass
            await page.wait_for_timeout(5000)
        
        logger.warning("⚠️ Playlist loading timeout, proceeding anyway")

    async def _select_spotify_destination(self, page):
        """Select Spotify as the destination platform"""
        spotify_selectors = [
            'button[data-id="1"]',  # Spotify's typical data-id
            'button[aria-label="Spotify"]',
            'button:has-text("Spotify")',
            '[class*="MusicServiceBlock"]:has-text("Spotify")',
            'button:has(img[alt*="Spotify"])'
        ]
        
        for selector in spotify_selectors:
            try:
                element = await page.wait_for_selector(selector, timeout=5000)
                if element:
                    await element.click()
                    await page.wait_for_timeout(2000)
                    logger.info("✅ Spotify destination selected")
                    return
            except:
                continue
        
        raise Exception("Could not find Spotify destination button")

    async def _configure_transfer_settings(self, page):
        """Configure transfer settings (select all tracks, etc.)"""
        try:
            # Look for "Select All" button or checkbox
            select_all_selectors = [
                'button:has-text("Select all")',
                'button:has-text("All")',
                'input[type="checkbox"][class*="select-all"]',
                '[class*="select-all"]'
            ]
            
            for selector in select_all_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        await page.wait_for_timeout(1000)
                        logger.info("✅ All tracks selected")
                        break
                except:
                    continue
            
        except Exception as e:
            logger.warning(f"Could not configure all transfer settings: {e}")

    async def _start_transfer(self, page):
        """Start the actual transfer process"""
        transfer_selectors = [
            'button:has-text("Start moving my music")',
            'button:has-text("Transfer")',
            'button:has-text("Start")',
            'button[class*="transfer"]',
            'button[type="submit"]'
        ]
        
        for selector in transfer_selectors:
            try:
                button = await page.wait_for_selector(selector, timeout=5000)
                if button:
                    await button.click()
                    await page.wait_for_timeout(3000)
                    logger.info("✅ Transfer started")
                    return {"started": True}
            except:
                continue
        
        raise Exception("Could not find transfer start button")

    async def _wait_for_completion(self, page):
        """Wait for transfer completion and extract results"""
        logger.info("⏳ Waiting for transfer to complete...")
        
        completion_selectors = [
            ':has-text("Transfer completed")',
            ':has-text("Done")',
            ':has-text("Finished")',
            '[class*="completed"]',
            '[class*="success"]'
        ]
        
        tracks_migrated = 0
        tracks_unmigrated = 0
        spotify_url = ""
        
        # Wait up to 10 minutes for completion
        for minute in range(10):
            logger.info(f"⏳ Waiting... ({minute + 1}/10 minutes)")
            
            # Check for completion
            for selector in completion_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=10000)
                    if element:
                        logger.info("✅ Transfer completed!")
                        
                        # Try to extract statistics
                        try:
                            transferred_text = await page.inner_text(':has-text("transferred")')
                            import re
                            migrated_match = re.search(r'(\d+).*transferred', transferred_text.lower())
                            if migrated_match:
                                tracks_migrated = int(migrated_match.group(1))
                        except:
                            pass
                        
                        try:
                            unmigrated_text = await page.inner_text(':has-text("not found")')
                            import re
                            unmigrated_match = re.search(r'(\d+).*not found', unmigrated_text.lower())
                            if unmigrated_match:
                                tracks_unmigrated = int(unmigrated_match.group(1))
                        except:
                            pass
                        
                        try:
                            spotify_link = await page.query_selector('a[href*="open.spotify.com/playlist"]')
                            if spotify_link:
                                spotify_url = await spotify_link.get_attribute('href')
                        except:
                            pass
                        
                        return {
                            "completed": True,
                            "tracks_migrated": tracks_migrated,
                            "tracks_unmigrated": tracks_unmigrated,
                            "spotify_url": spotify_url
                        }
                except:
                    continue
            
            await page.wait_for_timeout(60000)  # Wait 1 minute
        
        logger.warning("⚠️ Transfer timeout, but may have completed")
        return {
            "completed": False,
            "tracks_migrated": tracks_migrated,
            "tracks_unmigrated": tracks_unmigrated,
            "spotify_url": spotify_url
        }

    async def _download_unmigrated_csv(self, page, playlist_id: str):
        """Download CSV of unmigrated tracks if available"""
        try:
            csv_selectors = [
                'button:has-text("Download CSV")',
                'a:has-text("Download")',
                'button:has-text("Export")',
                '[class*="download"]',
                '[href*=".csv"]'
            ]
            
            for selector in csv_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        # Set up download handling
                        download_promise = page.wait_for_download()
                        await element.click()
                        
                        download = await download_promise
                        csv_filename = f"unmigrated_tracks_{playlist_id}_{self.session_id}.csv"
                        csv_path = self.csv_dir / csv_filename
                        
                        await download.save_as(csv_path)
                        logger.info(f"✅ Downloaded unmigrated tracks CSV: {csv_path}")
                        
                        return {"csv_file": str(csv_path)}
                except:
                    continue
            
            logger.info("ℹ️ No CSV download option found")
            return {"csv_file": ""}
            
        except Exception as e:
            logger.warning(f"Could not download CSV: {e}")
            return {"csv_file": ""}

    async def _generate_final_report(self):
        """Generate final migration report"""
        duration = self.stats["end_time"] - self.stats["start_time"]
        
        report = f"""
🎉 TuneMyMusic Migration Session Complete!

📊 SESSION STATISTICS:
{'='*50}
Session ID: {self.session_id}
Duration: {duration}
Start Time: {self.stats['start_time']}
End Time: {self.stats['end_time']}

📋 MIGRATION RESULTS:
{'='*50}
Total Playlists: {self.stats['total_playlists']}
✅ Successful Transfers: {self.stats['successful_transfers']}
❌ Failed Transfers: {self.stats['failed_transfers']}
⏭️ Skipped Duplicates: {self.stats['skipped_duplicates']}

🎵 TRACK STATISTICS:
{'='*50}
Total Tracks Migrated: {self.stats['total_tracks_migrated']}
Total Tracks Unmigrated: {self.stats['total_tracks_unmigrated']}
Success Rate: {(self.stats['total_tracks_migrated'] / (self.stats['total_tracks_migrated'] + self.stats['total_tracks_unmigrated']) * 100) if (self.stats['total_tracks_migrated'] + self.stats['total_tracks_unmigrated']) > 0 else 0:.1f}%

📁 FILES GENERATED:
{'='*50}
Session Log: {self.session_log}
Screenshots: {self.screenshots_dir}
Unmigrated CSVs: {self.csv_dir}
Processed Playlists: {self.processed_file}
"""
        
        print(report)
        self._log_session(report)
        
        # Save detailed report
        report_file = self.logs_dir / f"migration_report_{self.session_id}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 Detailed report saved: {report_file}")

async def main():
    """Main function for batch playlist migration"""
    import sys
    
    automation = TuneMyMusicAutomation()
    
    print("🎵 TuneMyMusic Automation - Anghami to Spotify Migration")
    print("=" * 60)
    
    # Get playlist URLs
    if len(sys.argv) > 1:
        # URLs provided as arguments
        playlist_urls = sys.argv[1:]
    else:
        # Interactive input
        print("Enter Anghami playlist URLs (one per line, empty line to finish):")
        playlist_urls = []
        while True:
            url = input().strip()
            if not url:
                break
            playlist_urls.append(url)
    
    if not playlist_urls:
        print("❌ No playlist URLs provided")
        return
    
    print(f"\n🚀 Starting migration of {len(playlist_urls)} playlists...")
    
    try:
        results = await automation.migrate_playlists(playlist_urls)
        print(f"\n✅ Migration session completed!")
        print(f"📊 Final stats: {results['successful_transfers']}/{results['total_playlists']} successful")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 