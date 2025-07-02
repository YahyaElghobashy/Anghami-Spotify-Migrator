#!/usr/bin/env python3
"""
Configuration Manager

Centralized configuration for all hardcoded values, file paths, timeouts, and settings.
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ExtractorConfig:
    """Configuration for Anghami extractors"""
    
    # Browser settings
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    viewport_width: int = 1920
    viewport_height: int = 1080
    headless: bool = True
    
    # Timeouts (in milliseconds)
    page_load_timeout: int = 30000
    element_wait_timeout: int = 10000
    scroll_wait_timeout: int = 2000
    default_wait_timeout: int = 5000
    
    # Scrolling settings
    max_scroll_attempts: int = 50
    stable_scroll_iterations: int = 5
    
    # CSS Selectors for Anghami (with fallbacks)
    playlist_name_selectors: List[str] = field(default_factory=lambda: [
        'h1[_ngcontent-anghami-web-v2-c186]',
        'h1[class*=""]',
        'h1',
        '[class*="playlist-title"]',
        '[class*="playlistTitle"]',
        '.title',
        '[data-testid="playlist-title"]',
        'meta[property="og:title"]'
    ])
    
    description_selectors: List[str] = field(default_factory=lambda: [
        'p[_ngcontent-anghami-web-v2-c190]',
        '[class*="info-description"] p',
        '[class*="description"]',
        '[class*="bio"]',
        '[class*="about"]',
        'meta[name="description"]',
        'meta[property="og:description"]'
    ])
    
    cover_art_selectors: List[str] = field(default_factory=lambda: [
        'img.collection-cover-img',
        'img[class*="collection-cover"]',
        'img[class*="cover"]',
        'img[class*="playlist"]',
        'img[class*="album"]',
        '[class*="image"] img',
        '.artwork img',
        'meta[property="og:image"]'
    ])
    
    creator_selectors: List[str] = field(default_factory=lambda: [
        'a[href*="/profile/"]',
        'a[anghamicheckarlang]',
        '[class*="creator"]',
        '[class*="user"]',
        'meta[name="author"]'
    ])
    
    track_count_selectors: List[str] = field(default_factory=lambda: [
        'div.font-weight-bold.value',
        '[class*="font-weight-bold"] [class*="value"]',
        '[class*="track-count"]',
        '[class*="song-count"]'
    ])
    
    track_row_selector: str = 'a.table-row.no-style-link'
    track_title_selector: str = '.cell.cell-title span'
    track_artist_selector: str = '.cell.cell-artist a'
    
    # File paths
    screenshot_filename: str = "anghami_loaded.png"
    debug_content_filename: str = "anghami_debug_content.html"

@dataclass 
class SpotifyConfig:
    """Configuration for Spotify API"""
    
    # OAuth settings
    client_id: str = field(default_factory=lambda: os.getenv('SPOTIFY_CLIENT_ID', ''))
    client_secret: str = field(default_factory=lambda: os.getenv('SPOTIFY_CLIENT_SECRET', ''))
    redirect_uri: str = field(default_factory=lambda: os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback'))
    
    # API settings
    auth_timeout: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay_base: int = 2  # seconds
    
    # Rate limiting
    rate_limit_delay: int = 1  # Default delay between requests
    max_tracks_per_request: int = 100  # Spotify's limit
    
    # Scopes required
    scopes: List[str] = field(default_factory=lambda: [
        "playlist-read-private",
        "playlist-modify-private", 
        "playlist-modify-public",
        "ugc-image-upload"
    ])
    
    # Cover art settings
    max_cover_art_size: int = 256000  # 256KB limit
    cover_art_format: str = "JPEG"
    max_cover_art_dimension: int = 1080

@dataclass
class DirectoryConfig:
    """Configuration for directory structure"""
    
    # Base directories
    project_root: Path = field(default_factory=lambda: Path.cwd())
    src_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    
    # Data subdirectories
    playlists_dir: Path = field(init=False)
    cover_art_dir: Path = field(init=False)
    screenshots_dir: Path = field(init=False)
    logs_dir: Path = field(init=False)
    
    # Config and temp
    config_dir: Path = field(init=False)
    temp_dir: Path = field(init=False)
    
    def __post_init__(self):
        """Initialize directory paths"""
        self.src_dir = self.project_root / "src"
        self.data_dir = self.project_root / "data"
        
        self.playlists_dir = self.data_dir / "playlists"
        self.cover_art_dir = self.data_dir / "cover_art"
        self.screenshots_dir = self.data_dir / "screenshots"
        self.logs_dir = self.data_dir / "logs"
        
        self.config_dir = self.project_root / "config"
        self.temp_dir = self.data_dir / "temp"
        
        # Create directories if they don't exist
        for directory in [
            self.src_dir, self.data_dir, self.playlists_dir, 
            self.cover_art_dir, self.screenshots_dir, self.logs_dir,
            self.config_dir, self.temp_dir
        ]:
            directory.mkdir(parents=True, exist_ok=True)

@dataclass
class TuneMyMusicConfig:
    """Configuration for TuneMyMusic proxy extractor"""
    
    base_url: str = "https://www.tunemymusic.com"
    transfer_url: str = "https://www.tunemymusic.com/transfer"
    
    # Selectors
    anghami_button_selector: str = 'button[data-id="3"]'
    url_input_selector: str = 'input[placeholder*="playlist"]'
    load_button_selector: str = 'button:has-text("Load my music")'
    
    track_row_selector: str = '.PlayListRow_row__1n_NK'
    track_name_selector: str = '.PlayListRow_innerName__ErNgP'
    track_artist_selector: str = '.PlayListRow_innerArtist__GPUeU'
    
    # Timeouts
    navigation_timeout: int = 30000
    load_timeout: int = 60000

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.extractor = ExtractorConfig()
        self.spotify = SpotifyConfig()
        self.directories = DirectoryConfig()
        self.tunemymusic = TuneMyMusicConfig()
        
        # Validate required settings
        self._validate_config()
    
    def _validate_config(self):
        """Validate configuration settings"""
        if not self.spotify.client_id or not self.spotify.client_secret:
            print("⚠️ Warning: Spotify credentials not configured. Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET environment variables.")
    
    def get_playlist_filename(self, playlist_id: str, extractor_type: str) -> str:
        """Generate standardized playlist filename"""
        return f"playlist_{playlist_id}_{extractor_type}.json"
    
    def get_cover_art_filename(self, playlist_id: str, extension: str = "webp") -> str:
        """Generate standardized cover art filename"""
        return f"cover_art_{playlist_id}.{extension}"
    
    def get_screenshot_filename(self, playlist_id: str = None) -> str:
        """Generate screenshot filename"""
        if playlist_id:
            return f"screenshot_{playlist_id}.png"
        return self.extractor.screenshot_filename

# Global configuration instance
config = Config()

def get_config() -> Config:
    """Get the global configuration instance"""
    return config 