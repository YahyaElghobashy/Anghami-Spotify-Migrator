#!/usr/bin/env python3
"""
Anghami User Playlist Discoverer
Discovers all playlists (created and followed) from an Anghami user profile
Works by navigating to sectionId=5 (created) and sectionId=10 (followed)
"""

import asyncio
import json
import logging
import re
import time
from urllib.parse import urlparse, urljoin
from pathlib import Path
from playwright.async_api import async_playwright
from typing import List, Dict, Optional
from dataclasses import dataclass
from dataclasses_json import dataclass_json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass_json
@dataclass
class AnghamiPlaylistSummary:
    """Summary information about a playlist discovered from user profile"""
    id: str
    name: str
    url: str
    description: str = ""
    cover_art_url: str = ""
    playlist_type: str = ""  # "created" or "followed"

@dataclass_json
@dataclass
class AnghamiUserPlaylists:
    """Collection of user's playlists"""
    user_id: str
    user_url: str
    created_playlists: List[AnghamiPlaylistSummary]
    followed_playlists: List[AnghamiPlaylistSummary]
    total_created: int
    total_followed: int

class AnghamiUserPlaylistDiscoverer:
    def __init__(self):
        self.output_dir = Path("data/playlists")
        self.screenshots_dir = Path("data/screenshots")
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        
    async def discover_user_playlists(self, profile_url: str) -> AnghamiUserPlaylists:
        """Discover all playlists (created and followed) from user profile"""
        logger.info(f"Starting playlist discovery for: {profile_url}")
        
        user_id = self._extract_user_id(profile_url)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,  # Headless mode for production
                args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                # Discover created playlists (sectionId=5)
                created_playlists = await self._discover_created_playlists(page, profile_url, user_id)
                
                # Discover followed playlists (sectionId=10)  
                followed_playlists = await self._discover_followed_playlists(page, profile_url, user_id)
                
                # Create result object
                user_playlists = AnghamiUserPlaylists(
                    user_id=user_id,
                    user_url=profile_url,
                    created_playlists=created_playlists,
                    followed_playlists=followed_playlists,
                    total_created=len(created_playlists),
                    total_followed=len(followed_playlists)
                )
                
                # Save results
                await self._save_results(user_playlists)
                
                return user_playlists
                
            except Exception as e:
                logger.error(f"Error discovering playlists: {e}")
                raise
            finally:
                await browser.close()
    
    async def _smart_load_all_playlists(self, page):
        """Smart detection system to efficiently load ALL playlists"""
        logger.info("🧠 Starting intelligent playlist loading detection...")
        
        # Phase 1: Setup monitoring systems
        await self._setup_smart_monitoring(page)
        
        # Phase 2: Intelligent scrolling with real-time feedback
        total_loaded = await self._intelligent_scroll_with_monitoring(page)
        
        # Phase 3: Final verification
        await self._verify_complete_loading(page)
        
        logger.info(f"🎯 Smart loading complete! Total playlists detected: {total_loaded}")
        return total_loaded
    
    async def _setup_smart_monitoring(self, page):
        """Setup DOM observers and network monitoring"""
        logger.info("🔧 Setting up smart monitoring systems...")
        
        # Setup DOM mutation observer to track playlist additions
        await page.evaluate("""
            window.playlistMonitor = {
                totalPlaylists: 0,
                lastChangeTime: Date.now(),
                isLoading: false,
                loadingStable: false,
                mutationCount: 0,
                networkRequests: 0,
                completedRequests: 0
            };
            
            // DOM Mutation Observer
            window.playlistObserver = new MutationObserver((mutations) => {
                let playlistsAdded = 0;
                mutations.forEach(mutation => {
                    if (mutation.type === 'childList') {
                        // Count new playlist elements
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1) { // Element node
                                if (node.matches?.('a.table-row.no-style-link, .card-item, [class*="playlist"]') ||
                                    node.querySelector?.('a.table-row.no-style-link, .card-item, [class*="playlist"]')) {
                                    playlistsAdded++;
                                }
                            }
                        });
                    }
                });
                
                if (playlistsAdded > 0) {
                    window.playlistMonitor.totalPlaylists += playlistsAdded;
                    window.playlistMonitor.lastChangeTime = Date.now();
                    window.playlistMonitor.mutationCount++;
                    console.log(`🎵 DOM: +${playlistsAdded} playlists (total: ${window.playlistMonitor.totalPlaylists})`);
                }
            });
            
            // Start observing
            window.playlistObserver.observe(document.body, {
                childList: true,
                subtree: true,
                attributes: false
            });
            
            // Simplified Network Request Monitoring (avoiding XMLHttpRequest issues)
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                window.playlistMonitor.networkRequests++;
                window.playlistMonitor.isLoading = true;
                return originalFetch.apply(this, args).finally(() => {
                    window.playlistMonitor.completedRequests++;
                    if (window.playlistMonitor.networkRequests === window.playlistMonitor.completedRequests) {
                        setTimeout(() => {
                            if (window.playlistMonitor.networkRequests === window.playlistMonitor.completedRequests) {
                                window.playlistMonitor.isLoading = false;
                            }
                        }, 500);  // Reduced timeout for faster detection
                    }
                });
            };
            
            // Simple activity detector instead of XMLHttpRequest override
            let activityTimeout;
            const resetActivityTimer = () => {
                window.playlistMonitor.isLoading = true;
                clearTimeout(activityTimeout);
                activityTimeout = setTimeout(() => {
                    window.playlistMonitor.isLoading = false;
                }, 1500);  // Consider inactive after 1.5s of no activity
            };
            
            // Monitor various activity indicators
            ['scroll', 'resize', 'load', 'DOMContentLoaded'].forEach(event => {
                window.addEventListener(event, resetActivityTimer, { passive: true });
            });
            
            // Monitor for image loading (indicates lazy loading)
            document.addEventListener('load', (e) => {
                if (e.target.tagName === 'IMG') {
                    resetActivityTimer();
                }
            }, true);
        """)
        
        # Wait for monitoring setup
        await page.wait_for_timeout(500)
        logger.info("✅ Smart monitoring systems active")
    
    async def _intelligent_scroll_with_monitoring(self, page):
        """Intelligent scrolling that adapts to real loading state"""
        logger.info("🎯 Starting intelligent scrolling with real-time detection...")
        
        last_playlist_count = 0
        stable_iterations = 0
        max_stable_iterations = 3  # Reduced from 5
        scroll_attempts = 0
        max_scroll_attempts = 20  # Reduced from 50 since we're smarter now
        no_change_count = 0
        max_no_change = 5  # Exit if no changes for 5 consecutive attempts
        
        while scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            # Get current state
            monitor_state = await page.evaluate("window.playlistMonitor")
            current_count = await self._count_playlist_elements(page)
            
            # Intelligent scroll with variable timing
            scroll_distance = min(800 + (scroll_attempts * 50), 2000)  # Smaller, more controlled scrolling
            await page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            
            # Smarter wait time - less sensitive to background activity
            if monitor_state["isLoading"] and scroll_attempts <= 3:
                wait_time = 1500  # Only wait longer for first few scrolls
                logger.info(f"   📊 Scroll {scroll_attempts}: Network active (early stage), waiting {wait_time/1000}s...")
            else:
                wait_time = 600   # Shorter wait most of the time
                logger.info(f"   📊 Scroll {scroll_attempts}: {current_count} playlists, quick check...")
            
            await page.wait_for_timeout(wait_time)
            
            # Check for completion indicators
            completion_check = await self._check_loading_completion(page)
            
            if completion_check["has_reached_end"]:
                logger.info(f"   🏁 Reached end indicator after {scroll_attempts} scrolls")
                break
            
            # Enhanced stability detection with timeout override
            if current_count > last_playlist_count:
                logger.info(f"   ✅ Found {current_count - last_playlist_count} new playlists (total: {current_count})")
                last_playlist_count = current_count
                stable_iterations = 0  # Reset stability counter
                no_change_count = 0    # Reset no-change counter
            else:
                stable_iterations += 1
                no_change_count += 1
                
                # Exit conditions (less strict about network activity)
                if stable_iterations >= max_stable_iterations:
                    if not monitor_state["isLoading"] or no_change_count >= max_no_change:
                        logger.info(f"   🔒 Content stable at {current_count} playlists (network idle or timeout)")
                        break
                    elif scroll_attempts >= 10:  # Give up on network detection after 10 attempts
                        logger.info(f"   ⏰ Content stable at {current_count} playlists (timeout override)")
                        break
                    else:
                        logger.info(f"   ⏳ Stable count but network active, continuing... ({no_change_count}/5)")
                        stable_iterations = max_stable_iterations - 1  # Give it more time
            
            # Early exit if we've found a reasonable number and no changes for a while
            if current_count > 10 and no_change_count >= max_no_change:
                logger.info(f"   🎯 Found {current_count} playlists with no changes for {no_change_count} attempts - completing")
                break
                
            # Emergency scroll to bottom less frequently
            if scroll_attempts % 15 == 0:
                logger.info(f"   🚀 Emergency scroll to bottom (attempt {scroll_attempts})")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
        
        final_count = await self._count_playlist_elements(page)
        logger.info(f"✅ Intelligent scrolling complete: {final_count} playlists loaded in {scroll_attempts} attempts")
        return final_count
    
    async def _check_loading_completion(self, page):
        """Check various indicators that loading is complete"""
        return await page.evaluate("""
            (() => {
                // Check for loading indicators
                const loadingSpinners = document.querySelectorAll('[class*="loading"], [class*="spinner"], .loader, [data-loading="true"]');
                const skeletonLoaders = document.querySelectorAll('[class*="skeleton"], [class*="placeholder"]');
                
                // Check for "Load More" or pagination buttons
                const loadMoreButtons = document.querySelectorAll('button[class*="load"], button[class*="more"], .pagination-next');
                const hasActiveLoadMore = Array.from(loadMoreButtons).some(btn => !btn.disabled && btn.offsetParent !== null);
                
                // Check scroll position relative to document height
                const scrollPosition = window.scrollY + window.innerHeight;
                const documentHeight = document.body.scrollHeight;
                const nearBottom = scrollPosition >= documentHeight - 200;
                
                // Check for infinite scroll triggers
                const infiniteScrollTriggers = document.querySelectorAll('[class*="infinite"], [data-infinite="true"]');
                
                // Check for empty state or "no more" indicators
                const endIndicators = document.querySelectorAll('[class*="no-more"], [class*="end-of"], [class*="all-loaded"]');
                
                return {
                    has_loading_spinners: loadingSpinners.length > 0,
                    has_skeleton_loaders: skeletonLoaders.length > 0,
                    has_active_load_more: hasActiveLoadMore,
                    near_bottom: nearBottom,
                    has_infinite_triggers: infiniteScrollTriggers.length > 0,
                    has_end_indicators: endIndicators.length > 0,
                    loading_indicators_gone: loadingSpinners.length === 0 && skeletonLoaders.length === 0,
                    has_reached_end: nearBottom && !hasActiveLoadMore && endIndicators.length > 0
                };
            })()
        """)
    
    async def _verify_complete_loading(self, page):
        """Final verification that all content is loaded"""
        logger.info("🔍 Final verification of complete loading...")
        
        # Wait for any remaining network activity to settle
        await page.wait_for_timeout(1000)
        
        # Check final state
        final_state = await page.evaluate("""
            ({
                totalPlaylists: window.playlistMonitor?.totalPlaylists || 0,
                isLoading: window.playlistMonitor?.isLoading || false,
                networkRequests: window.playlistMonitor?.networkRequests || 0,
                completedRequests: window.playlistMonitor?.completedRequests || 0,
                mutationCount: window.playlistMonitor?.mutationCount || 0
            })
        """)
        
        logger.info(f"📊 Final state: {final_state['totalPlaylists']} playlists, " +
                   f"{final_state['mutationCount']} DOM changes, " +
                   f"Network: {final_state['completedRequests']}/{final_state['networkRequests']}")
        
        # Cleanup monitoring
        await page.evaluate("""
            if (window.playlistObserver) {
                window.playlistObserver.disconnect();
            }
        """)
        
        logger.info("✅ Smart loading verification complete")
    
    async def _count_playlist_elements(self, page):
        """Count current playlist elements efficiently"""
        return await page.evaluate("""
            document.querySelectorAll('a.table-row.no-style-link, .card-item, [href*="/playlist/"]').length
        """)
    
    async def _scroll_to_load_all_playlists(self, page):
        """Legacy method - replaced with smart loading"""
        return await self._smart_load_all_playlists(page)
    
    async def _discover_created_playlists(self, page, profile_url: str, user_id: str) -> List[AnghamiPlaylistSummary]:
        """Discover created playlists (sectionId=5) using table-row structure"""
        created_url = f"{profile_url}?sectionId=5"
        logger.info(f"🎵 Discovering created playlists: {created_url}")
        
        await page.goto(created_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)  # Longer initial wait
        
        # Take screenshot for debugging
        screenshot_path = self.screenshots_dir / f"created_playlists_{user_id}_{int(time.time())}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"📸 Screenshot saved: {screenshot_path}")
        
        # Smart loading to load ALL content
        await self._smart_load_all_playlists(page)
        
        playlists = []
        
        try:
            # Wait for playlist section to load
            await page.wait_for_selector('#section-5', timeout=15000)
            logger.info("✅ Found created playlists section")
            
            # Find all playlist rows using the table-row structure
            playlist_elements = await page.query_selector_all('a.table-row.no-style-link[href*="/playlist/"]')
            logger.info(f"🔍 Found {len(playlist_elements)} created playlist elements")
            
            for i, element in enumerate(playlist_elements):
                try:
                    # Extract playlist URL and ID
                    href = await element.get_attribute('href')
                    if not href or '/playlist/' not in href:
                        continue
                        
                    playlist_id = href.split('/playlist/')[-1].split('?')[0]
                    playlist_url = f"https://play.anghami.com{href}" if href.startswith('/') else href
                    
                    # Extract title from cell-title
                    title_element = await element.query_selector('.cell.cell-title span')
                    title = ""
                    if title_element:
                        title = await title_element.inner_text()
                        title = title.strip()
                    
                    # Extract description from cell with no-text-transform class
                    desc_element = await element.query_selector('.cell .cell-type-text.no-text-transform')
                    description = ""
                    if desc_element:
                        description = await desc_element.inner_text()
                        description = description.strip()
                    
                    # Extract cover art from background-image style
                    cover_element = await element.query_selector('.cell.cell-coverart .list-item-image')
                    cover_art_url = ""
                    if cover_element:
                        style = await cover_element.get_attribute('style')
                        if style and 'background-image: url(' in style:
                            # Extract URL from style="background-image: url('...')"
                            match = re.search(r'background-image: url\(["\']([^"\']+)["\']', style)
                            if match:
                                cover_art_url = match.group(1)
                    
                    if title and playlist_id:
                        playlist = AnghamiPlaylistSummary(
                            id=playlist_id,
                            name=title,
                            url=playlist_url,
                            description=description,
                            cover_art_url=cover_art_url,
                            playlist_type="created"
                        )
                        playlists.append(playlist)
                        logger.debug(f"✅ Created playlist {i+1}: {title} ({playlist_id})")
                    else:
                        logger.debug(f"⚠️  Skipped invalid playlist at position {i+1}")
                    
                except Exception as e:
                    logger.debug(f"❌ Error extracting created playlist {i+1}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"❌ Error finding created playlists section: {e}")
        
        logger.info(f"🎯 Successfully extracted {len(playlists)} created playlists")
        return playlists
    
    async def _discover_followed_playlists(self, page, profile_url: str, user_id: str) -> List[AnghamiPlaylistSummary]:
        """Discover followed playlists (sectionId=10) using card-item structure"""
        followed_url = f"{profile_url}?sectionId=10"
        logger.info(f"➕ Discovering followed playlists: {followed_url}")
        
        await page.goto(followed_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(5000)  # Longer initial wait
        
        # Take screenshot for debugging
        screenshot_path = self.screenshots_dir / f"followed_playlists_{user_id}_{int(time.time())}.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"📸 Screenshot saved: {screenshot_path}")
        
        # Smart loading to load ALL content
        await self._smart_load_all_playlists(page)
        
        playlists = []
        
        try:
            # Wait for playlist section to load
            await page.wait_for_selector('#section-10', timeout=15000)
            logger.info("✅ Found followed playlists section")
            
            # Find all card items using the card structure
            card_elements = await page.query_selector_all('card-item a.card-item-image-container[href*="/playlist/"]')
            logger.info(f"🔍 Found {len(card_elements)} followed playlist card elements")
            
            for i, element in enumerate(card_elements):
                try:
                    # Extract playlist URL and ID
                    href = await element.get_attribute('href')
                    if not href or '/playlist/' not in href:
                        continue
                        
                    playlist_id = href.split('/playlist/')[-1].split('?')[0]
                    playlist_url = f"https://play.anghami.com{href}" if href.startswith('/') else href
                    
                    # Navigate to parent card-item to get title and description
                    card_item = await element.evaluate_handle('element => element.closest("card-item")')
                    
                    # Extract title from card-item-title
                    title_element = await card_item.query_selector('a.card-item-title')
                    title = ""
                    if title_element:
                        title = await title_element.inner_text()
                        title = title.strip()
                    
                    # Extract description from card-item-subtitle
                    desc_element = await card_item.query_selector('.card-item-subtitle')
                    description = ""
                    if desc_element:
                        description = await desc_element.inner_text()
                        description = description.strip()
                    
                    # Extract cover art from card-item-image background-image
                    cover_element = await element.query_selector('.card-item-image')
                    cover_art_url = ""
                    if cover_element:
                        style = await cover_element.get_attribute('style')
                        if style and 'background-image: url(' in style:
                            # Extract URL from style="background-image: url('...')"
                            match = re.search(r'background-image: url\(["\']([^"\']+)["\']', style)
                            if match:
                                cover_art_url = match.group(1)
                    
                    if title and playlist_id:
                        playlist = AnghamiPlaylistSummary(
                            id=playlist_id,
                            name=title,
                            url=playlist_url,
                            description=description,
                            cover_art_url=cover_art_url,
                            playlist_type="followed"
                        )
                        playlists.append(playlist)
                        logger.debug(f"✅ Followed playlist {i+1}: {title} ({playlist_id})")
                    else:
                        logger.debug(f"⚠️  Skipped invalid playlist at position {i+1}")
                    
                except Exception as e:
                    logger.debug(f"❌ Error extracting followed playlist {i+1}: {e}")
                    continue
                    
        except Exception as e:
            logger.warning(f"❌ Error finding followed playlists section: {e}")
        
        logger.info(f"🎯 Successfully extracted {len(playlists)} followed playlists")
        return playlists
    
    async def _save_results(self, user_playlists: AnghamiUserPlaylists):
        """Save discovered playlists to JSON file"""
        timestamp = int(time.time())
        filename = f"discovered_playlists_{user_playlists.user_id}_{timestamp}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(user_playlists.to_dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {filepath}")
    
    def _extract_user_id(self, profile_url: str) -> str:
        """Extract user ID from profile URL"""
        try:
            return profile_url.split('/profile/')[-1].split('?')[0]
        except:
            return str(int(time.time()))

async def main():
    """Main function to test the discoverer"""
    import sys
    
    discoverer = AnghamiUserPlaylistDiscoverer()
    
    # Get URL from command line argument or prompt user
    if len(sys.argv) > 1:
        profile_url = sys.argv[1]
    else:
        profile_url = input("Enter Anghami profile URL: ").strip()
        if not profile_url:
            print("❌ No profile URL provided")
            return
    
    try:
        user_playlists = await discoverer.discover_user_playlists(profile_url)
        
        print(f"\n✅ Playlist discovery completed!")
        print(f"👤 User ID: {user_playlists.user_id}")
        print(f"📀 Created playlists: {user_playlists.total_created}")
        print(f"➕ Followed playlists: {user_playlists.total_followed}")
        print(f"🔢 Total playlists: {user_playlists.total_created + user_playlists.total_followed}")
        
        if user_playlists.created_playlists:
            print(f"\n🎵 Created Playlists:")
            for i, playlist in enumerate(user_playlists.created_playlists[:10]):
                desc = f" - {playlist.description[:50]}..." if playlist.description else ""
                print(f"  {i+1}. {playlist.name}{desc}")
            if len(user_playlists.created_playlists) > 10:
                print(f"  ... and {len(user_playlists.created_playlists) - 10} more")
        
        if user_playlists.followed_playlists:
            print(f"\n➕ Followed Playlists:")
            for i, playlist in enumerate(user_playlists.followed_playlists[:10]):
                desc = f" - {playlist.description[:50]}..." if playlist.description else ""
                print(f"  {i+1}. {playlist.name}{desc}")
            if len(user_playlists.followed_playlists) > 10:
                print(f"  ... and {len(user_playlists.followed_playlists) - 10} more")
        
    except Exception as e:
        print(f"❌ Playlist discovery failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 