#!/usr/bin/env python3
"""
Spotify Track Matching Engine

Advanced track matching system for Anghami to Spotify migration with:
- Multi-strategy search (exact → normalized → fuzzy)
- Confidence scoring system (0.0-1.0)
- Arabic/Unicode text handling
- Rate limiting and result caching
- Intelligent fallback strategies
"""

import asyncio
import json
import re
import time
import unicodedata
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from dataclasses_json import dataclass_json
import logging

# Import from project structure
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
from src.auth.spotify_auth import create_spotify_auth
from src.models.anghami_models import AnghamiTrack, AnghamiPlaylist
from src.utils.config import get_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass_json
@dataclass
class SpotifyTrackMatch:
    """Represents a matched track from Spotify with confidence score"""
    
    spotify_id: str
    title: str
    artists: List[str]
    album: str
    duration_ms: int
    preview_url: Optional[str]
    external_urls: Dict[str, str]
    confidence_score: float
    match_strategy: str
    match_reasons: List[str] = field(default_factory=list)
    
    @property
    def primary_artist(self) -> str:
        """Get the primary (first) artist"""
        return self.artists[0] if self.artists else ""
    
    @property
    def all_artists_string(self) -> str:
        """Get all artists as a comma-separated string"""
        return ", ".join(self.artists)
    
    @property
    def duration_seconds(self) -> int:
        """Get duration in seconds"""
        return self.duration_ms // 1000 if self.duration_ms else 0
    
    @property
    def spotify_url(self) -> str:
        """Get Spotify web URL"""
        return self.external_urls.get('spotify', '')


@dataclass_json
@dataclass
class MatchResult:
    """Result of track matching operation"""
    
    anghami_track: AnghamiTrack
    spotify_matches: List[SpotifyTrackMatch] = field(default_factory=list)
    best_match: Optional[SpotifyTrackMatch] = None
    search_queries_tried: List[str] = field(default_factory=list)
    total_search_time_ms: int = 0
    error_message: Optional[str] = None
    is_arabic_track: bool = False
    requires_user_review: bool = False
    arabic_artist_variants_tried: List[str] = field(default_factory=list)
    discography_search_attempted: bool = False
    
    @property
    def has_match(self) -> bool:
        """Check if any matches were found"""
        return len(self.spotify_matches) > 0
    
    @property
    def has_confident_match(self) -> bool:
        """Check if a high-confidence match was found"""
        return self.best_match is not None and self.best_match.confidence_score >= 0.75
    
    @property
    def match_confidence(self) -> float:
        """Get the confidence of the best match"""
        return self.best_match.confidence_score if self.best_match else 0.0


class ArabicTransliterator:
    """Handles Arabic text transliteration and phonetic matching"""
    
    # Common Arabic to English transliteration patterns
    ARABIC_TRANSLITERATIONS = {
        'موسى': ['Moussa', 'Mousv', 'Mousa', 'Musa', 'Mousse', 'Mowsa'],
        'أحمد': ['Ahmed', 'Ahmad', 'Ahmet', 'Ahamad'],
        'محمد': ['Mohamed', 'Mohammed', 'Muhammad', 'Mohamad', 'Mahmoud'],
        'حسين': ['Hussein', 'Husyn', 'Hosein', 'Husain', 'Hussien'],
        'علي': ['Ali', 'Aly', 'Alee'],
        'عمر': ['Omar', 'Omer', 'Umar'],
        'خالد': ['Khaled', 'Khalid', 'Chalid'],
        'محمود': ['Mahmoud', 'Mahmud', 'Mahmod'],
        'يوسف': ['Youssef', 'Yusuf', 'Joseph', 'Yosef'],
        'كريم': ['Karim', 'Kareem', 'Kreem'],
        'رامي': ['Rami', 'Ramey', 'Rammy'],
        'سامي': ['Sami', 'Sammy', 'Samey'],
        'طارق': ['Tarek', 'Tariq', 'Tarik'],
        'وليد': ['Walid', 'Waleed', 'Waleed'],
        'هشام': ['Hisham', 'Hesham', 'Hicham'],
        'أمير': ['Amir', 'Ameer', 'Emir'],
        'فارس': ['Fares', 'Fars', 'Faris'],
        'مراد': ['Murad', 'Morad', 'Mrad'],
        'نادر': ['Nader', 'Nadir', 'Nadeer'],
        'وليد': ['Walid', 'Waleed', 'Waleed']
    }
    
    # Arabic phonetic patterns
    PHONETIC_PATTERNS = {
        'ش': ['sh', 'ch'],
        'خ': ['kh', 'ch', 'x'],
        'ج': ['j', 'g'],
        'ح': ['h', '7'],
        'ع': ['a', 'e', '3'],
        'غ': ['gh', 'g'],
        'ق': ['q', 'k'],
        'ص': ['s', 'z'],
        'ض': ['d', 'z'],
        'ط': ['t'],
        'ظ': ['z', 'th'],
        'ذ': ['th', 'z'],
        'ث': ['th', 's'],
        'ء': ['a', 'e', ''],
        'ى': ['a', 'e', 'i'],
        'و': ['w', 'u', 'o'],
        'ي': ['y', 'i', 'e']
    }
    
    @staticmethod
    def is_arabic_text(text: str) -> bool:
        """Check if text contains Arabic characters"""
        if not text:
            return False
        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        return arabic_chars > len(text) * 0.3  # 30% threshold
    
    @staticmethod
    def get_transliteration_variants(arabic_name: str) -> List[str]:
        """Get possible transliteration variants for Arabic name"""
        variants = []
        
        # Direct lookup in transliteration table
        if arabic_name in ArabicTransliterator.ARABIC_TRANSLITERATIONS:
            variants.extend(ArabicTransliterator.ARABIC_TRANSLITERATIONS[arabic_name])
        
        # Phonetic transliteration
        phonetic_variants = ArabicTransliterator._generate_phonetic_variants(arabic_name)
        variants.extend(phonetic_variants)
        
        # Remove duplicates and empty strings
        variants = list(set([v for v in variants if v.strip()]))
        
        return variants
    
    @staticmethod
    def _generate_phonetic_variants(arabic_text: str) -> List[str]:
        """Generate phonetic variants using pattern matching"""
        variants = []
        
        # Simple phonetic conversion
        phonetic = arabic_text
        for arabic_char, english_variants in ArabicTransliterator.PHONETIC_PATTERNS.items():
            if arabic_char in phonetic:
                for variant in english_variants:
                    new_variant = phonetic.replace(arabic_char, variant)
                    if new_variant != phonetic and len(new_variant) > 1:
                        variants.append(new_variant.title())
        
        return variants
    
    @staticmethod
    def fuzzy_match_arabic_name(arabic_name: str, english_candidates: List[str]) -> List[Tuple[str, float]]:
        """Fuzzy match Arabic name against English candidates"""
        if not arabic_name or not english_candidates:
            return []
        
        matches = []
        variants = ArabicTransliterator.get_transliteration_variants(arabic_name)
        
        for candidate in english_candidates:
            best_score = 0.0
            
            # Check direct variants
            for variant in variants:
                score = SequenceMatcher(None, variant.lower(), candidate.lower()).ratio()
                best_score = max(best_score, score)
            
            # Check phonetic similarity
            phonetic_score = ArabicTransliterator._phonetic_similarity(arabic_name, candidate)
            best_score = max(best_score, phonetic_score)
            
            if best_score > 0.4:  # Minimum threshold
                matches.append((candidate, best_score))
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    @staticmethod
    def _phonetic_similarity(arabic_text: str, english_text: str) -> float:
        """Calculate phonetic similarity between Arabic and English text"""
        if not arabic_text or not english_text:
            return 0.0
        
        # Basic phonetic matching
        variants = ArabicTransliterator.get_transliteration_variants(arabic_text)
        
        best_score = 0.0
        for variant in variants:
            score = SequenceMatcher(None, variant.lower(), english_text.lower()).ratio()
            best_score = max(best_score, score)
        
        return best_score


class TextNormalizer:
    """Handles text normalization for better matching across languages"""
    
    @staticmethod
    def normalize_unicode(text: str) -> str:
        """Normalize Unicode text by removing diacritics and normalizing forms"""
        if not text:
            return ""
        
        # Normalize Unicode to decomposed form
        normalized = unicodedata.normalize('NFD', text)
        
        # Remove diacritical marks
        without_diacritics = ''.join(
            char for char in normalized 
            if unicodedata.category(char) != 'Mn'
        )
        
        return without_diacritics.strip()
    
    @staticmethod
    def clean_search_text(text: str) -> str:
        """Clean text for search queries"""
        if not text:
            return ""
        
        # Normalize unicode
        text = TextNormalizer.normalize_unicode(text)
        
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^\w\s\-\'\.]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def extract_main_title(title: str) -> str:
        """Extract main title by removing featured artists and extra info"""
        if not title:
            return ""
        
        # Remove common patterns like (feat. Artist), [feat. Artist], etc.
        patterns = [
            r'\(feat\.?\s+[^)]+\)',
            r'\[feat\.?\s+[^\]]+\]',
            r'\(featuring\s+[^)]+\)',
            r'\s+feat\.?\s+.+$',
            r'\s+featuring\s+.+$',
            r'\s+ft\.?\s+.+$',
            r'\s+with\s+.+$',
            r'\([^)]*remix[^)]*\)',
            r'\([^)]*version[^)]*\)',
            r'\([^)]*edit[^)]*\)'
        ]
        
        cleaned_title = title
        for pattern in patterns:
            cleaned_title = re.sub(pattern, '', cleaned_title, flags=re.IGNORECASE)
        
        return cleaned_title.strip()
    
    @staticmethod
    def similarity_score(text1: str, text2: str) -> float:
        """Calculate similarity score between two text strings"""
        if not text1 or not text2:
            return 0.0
        
        # Normalize for comparison
        norm1 = TextNormalizer.clean_search_text(text1.lower())
        norm2 = TextNormalizer.clean_search_text(text2.lower())
        
        if norm1 == norm2:
            return 1.0
        
        # Use SequenceMatcher for similarity
        return SequenceMatcher(None, norm1, norm2).ratio()


class SpotifySearchCache:
    """Cache for Spotify search results to avoid redundant API calls"""
    
    def __init__(self, cache_duration_hours: int = 24):
        self.cache: Dict[str, Dict] = {}
        self.cache_duration = timedelta(hours=cache_duration_hours)
    
    def _get_cache_key(self, query: str, search_type: str) -> str:
        """Generate cache key for a search query"""
        return f"{search_type}:{query.lower().strip()}"
    
    def get(self, query: str, search_type: str = "track") -> Optional[Dict]:
        """Get cached search result"""
        key = self._get_cache_key(query, search_type)
        
        if key in self.cache:
            cached_item = self.cache[key]
            cached_time = cached_item.get('timestamp')
            
            if cached_time and datetime.now() - cached_time < self.cache_duration:
                return cached_item.get('data')
            else:
                # Remove expired cache entry
                del self.cache[key]
        
        return None
    
    def set(self, query: str, data: Dict, search_type: str = "track") -> None:
        """Cache search result"""
        key = self._get_cache_key(query, search_type)
        self.cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def clear_expired(self) -> None:
        """Clear expired cache entries"""
        now = datetime.now()
        expired_keys = [
            key for key, value in self.cache.items()
            if now - value.get('timestamp', now) > self.cache_duration
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'total_entries': len(self.cache),
            'expired_entries': len([
                key for key, value in self.cache.items()
                if datetime.now() - value.get('timestamp', datetime.now()) > self.cache_duration
            ])
        }


class SpotifyTrackMatcher:
    """Advanced Spotify track matching engine"""
    
    def __init__(self, config=None):
        self.config = config or get_config()
        self.spotify_auth = create_spotify_auth()
        self.cache = SpotifySearchCache()
        self.normalizer = TextNormalizer()
        self.arabic_transliterator = ArabicTransliterator()
        
        # Configuration - use defaults since migration config isn't in the Config class yet
        self.confidence_threshold = 0.75  # Default confidence threshold
        self.max_search_results = 10      # Default search results limit
        self.request_delay = 0.1           # Minimum delay between requests
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'successful_matches': 0,
            'high_confidence_matches': 0,
            'failed_searches': 0,
            'arabic_tracks_processed': 0,
            'arabic_tracks_matched': 0,
            'arabic_high_confidence': 0,
            'arabic_discography_searches': 0,
            'tracks_requiring_review': 0
        }
        
        # Rate limiting
        self.last_request_time = 0
        
        logger.info("🎯 Spotify Track Matcher initialized")
    
    def authenticate(self) -> bool:
        """Authenticate with Spotify API"""
        logger.info("🔐 Authenticating with Spotify...")
        return self.spotify_auth.authenticate()
    
    async def match_track(self, anghami_track: AnghamiTrack) -> MatchResult:
        """Match a single Anghami track with Spotify using enhanced Arabic matching"""
        start_time = time.time()
        result = MatchResult(anghami_track=anghami_track)
        
        # Detect Arabic track
        result.is_arabic_track = (
            self.arabic_transliterator.is_arabic_text(anghami_track.title) or
            any(self.arabic_transliterator.is_arabic_text(artist) for artist in anghami_track.artists)
        )
        
        if result.is_arabic_track:
            logger.info(f"🌍 [ARABIC] Matching track: '{anghami_track.title}' by {anghami_track.primary_artist}")
        else:
            logger.info(f"🔍 Matching track: '{anghami_track.title}' by {anghami_track.primary_artist}")
        
        try:
            # Arabic tracks get special treatment
            if result.is_arabic_track:
                success = await self._match_arabic_track(anghami_track, result)
                if not success:
                    logger.info(f"   🔄 Arabic matching failed, falling back to general search")
                    await self._match_general_track(anghami_track, result)
            else:
                await self._match_general_track(anghami_track, result)
            
            # Process results and set flags
            await self._finalize_match_result(anghami_track, result)
            
        except Exception as e:
            logger.error(f"   💥 Error matching track: {e}")
            result.error_message = str(e)
            self.stats['failed_searches'] += 1
        
        result.total_search_time_ms = int((time.time() - start_time) * 1000)
        self.stats['total_searches'] += 1
        
        return result
    
    async def _match_arabic_track(self, anghami_track: AnghamiTrack, result: MatchResult) -> bool:
        """Enhanced Arabic track matching with artist-first approach"""
        logger.info(f"   🎭 Starting Arabic artist identification...")
        
        # Step 1: Try to identify the Arabic artist on Spotify
        identified_artists = await self._identify_arabic_artist(anghami_track.primary_artist)
        
        if identified_artists:
            logger.info(f"   ✅ Found {len(identified_artists)} potential artist matches")
            result.arabic_artist_variants_tried = [artist[0] for artist in identified_artists[:3]]
            
            # Step 2: Search through identified artists' discographies
            for artist_name, confidence in identified_artists[:3]:  # Try top 3 matches
                logger.info(f"   🎵 Searching {artist_name}'s discography (confidence: {confidence:.2f})")
                
                discography_matches = await self._search_artist_discography(artist_name, anghami_track.title)
                if discography_matches:
                    result.discography_search_attempted = True
                    scored_matches = self._score_matches(anghami_track, discography_matches, f"discography_{artist_name}")
                    result.spotify_matches.extend(scored_matches)
                    
                    # Check if we found a good match
                    best_discography_match = max(scored_matches, key=lambda x: x.confidence_score) if scored_matches else None
                    if best_discography_match and best_discography_match.confidence_score >= 0.6:  # Lower threshold for Arabic
                        logger.info(f"   🎯 Good discography match found: {best_discography_match.confidence_score:.2f}")
                        return True
        
        # Step 3: If artist identification failed, try general Arabic search
        logger.info(f"   🔍 Trying general Arabic search strategies...")
        return False  # Continue with fallback
    
    async def _identify_arabic_artist(self, arabic_artist_name: str) -> List[Tuple[str, float]]:
        """Identify Arabic artist on Spotify using transliteration"""
        if not arabic_artist_name:
            return []
        
        # Get transliteration variants
        variants = self.arabic_transliterator.get_transliteration_variants(arabic_artist_name)
        logger.info(f"   🔤 Generated variants for '{arabic_artist_name}': {variants[:5]}...")  # Show first 5
        
        identified_artists = []
        
        # Search for each variant
        for variant in variants[:8]:  # Limit to avoid too many API calls
            try:
                artist_results = await self._search_spotify_artists(variant)
                if artist_results:
                    # Score the artist matches
                    for artist_data in artist_results:
                        artist_name = artist_data.get('name', '')
                        similarity = self.arabic_transliterator._phonetic_similarity(arabic_artist_name, artist_name)
                        
                        if similarity > 0.5:  # Reasonable threshold
                            identified_artists.append((artist_name, similarity))
                            logger.debug(f"     📝 Found artist: {artist_name} (similarity: {similarity:.2f})")
                
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.warning(f"   ⚠️ Error searching for variant '{variant}': {e}")
                continue
        
        # Remove duplicates and sort by confidence
        unique_artists = {}
        for name, score in identified_artists:
            if name not in unique_artists or unique_artists[name] < score:
                unique_artists[name] = score
        
        sorted_artists = [(name, score) for name, score in unique_artists.items()]
        sorted_artists.sort(key=lambda x: x[1], reverse=True)
        
        return sorted_artists[:5]  # Return top 5
    
    async def _search_spotify_artists(self, artist_name: str) -> List[Dict]:
        """Search for artists on Spotify"""
        try:
            response = self.spotify_auth.make_authenticated_request(
                'GET',
                'https://api.spotify.com/v1/search',
                params={
                    'q': f'artist:"{artist_name}"',
                    'type': 'artist',
                    'limit': 5,
                    'market': 'US'
                }
            )
            
            search_data = response.json()
            return search_data.get('artists', {}).get('items', [])
            
        except Exception as e:
            logger.debug(f"   ⚠️ Artist search failed for '{artist_name}': {e}")
            return []
    
    async def _search_artist_discography(self, artist_name: str, track_title: str) -> List[Dict]:
        """Search through an artist's discography for a specific track"""
        try:
            # First get the artist ID
            artist_results = await self._search_spotify_artists(artist_name)
            if not artist_results:
                return []
            
            artist_id = artist_results[0].get('id')
            if not artist_id:
                return []
            
            # Get artist's albums
            response = self.spotify_auth.make_authenticated_request(
                'GET',
                f'https://api.spotify.com/v1/artists/{artist_id}/albums',
                params={
                    'include_groups': 'album,single',
                    'market': 'US',
                    'limit': 20  # Limit to avoid too many API calls
                }
            )
            
            albums_data = response.json()
            albums = albums_data.get('items', [])
            
            # Search through album tracks
            matching_tracks = []
            for album in albums[:10]:  # Limit albums to search
                album_id = album.get('id')
                if not album_id:
                    continue
                
                # Get album tracks
                tracks_response = self.spotify_auth.make_authenticated_request(
                    'GET',
                    f'https://api.spotify.com/v1/albums/{album_id}/tracks',
                    params={'market': 'US'}
                )
                
                tracks_data = tracks_response.json()
                tracks = tracks_data.get('items', [])
                
                # Check each track title
                for track in tracks:
                    track_name = track.get('name', '')
                    similarity = self.normalizer.similarity_score(track_title, track_name)
                    
                    if similarity > 0.4:  # Reasonable threshold for Arabic tracks
                        # Convert to full track object format
                        full_track = {
                            'id': track.get('id'),
                            'name': track_name,
                            'artists': track.get('artists', []),
                            'album': album,
                            'duration_ms': track.get('duration_ms', 0),
                            'preview_url': track.get('preview_url'),
                            'external_urls': track.get('external_urls', {})
                        }
                        matching_tracks.append(full_track)
                
                await asyncio.sleep(0.1)  # Rate limiting between albums
            
            return matching_tracks
            
        except Exception as e:
            logger.warning(f"   ⚠️ Discography search failed for '{artist_name}': {e}")
            return []
    
    async def _match_general_track(self, anghami_track: AnghamiTrack, result: MatchResult):
        """General track matching using multiple strategies"""
        search_strategies = self._generate_search_strategies(anghami_track)
        
        # Try each strategy until we find a good match
        for strategy_name, query in search_strategies:
            logger.debug(f"   Trying {strategy_name}: {query}")
            result.search_queries_tried.append(f"{strategy_name}: {query}")
            
            matches = await self._search_spotify(query, strategy_name)
            if matches:
                # Score and filter matches
                scored_matches = self._score_matches(anghami_track, matches, strategy_name)
                result.spotify_matches.extend(scored_matches)
                
                # Check if we found a high-confidence match
                best_in_strategy = max(scored_matches, key=lambda x: x.confidence_score) if scored_matches else None
                if best_in_strategy and best_in_strategy.confidence_score >= self.confidence_threshold:
                    logger.info(f"   ✅ High confidence match found with {strategy_name}")
                    break
            
            # Small delay between strategies
            await asyncio.sleep(0.1)
    
    async def _finalize_match_result(self, anghami_track: AnghamiTrack, result: MatchResult):
        """Finalize match result and set appropriate flags"""
        
        # Update Arabic-specific statistics
        if result.is_arabic_track:
            self.stats['arabic_tracks_processed'] += 1
            if result.discography_search_attempted:
                self.stats['arabic_discography_searches'] += 1
        
        # Select best match
        if result.spotify_matches:
            result.best_match = max(result.spotify_matches, key=lambda x: x.confidence_score)
            self.stats['successful_matches'] += 1
            
            # Update Arabic match statistics
            if result.is_arabic_track:
                self.stats['arabic_tracks_matched'] += 1
            
            # Determine if user review is needed
            confidence = result.best_match.confidence_score
            
            if confidence >= self.confidence_threshold:
                self.stats['high_confidence_matches'] += 1
                if result.is_arabic_track:
                    self.stats['arabic_high_confidence'] += 1
                    logger.info(f"   🎯 [ARABIC] Best match: '{result.best_match.title}' by {result.best_match.primary_artist} "
                              f"(confidence: {confidence:.2f})")
                else:
                    logger.info(f"   🎯 Best match: '{result.best_match.title}' by {result.best_match.primary_artist} "
                              f"(confidence: {confidence:.2f})")
            else:
                # Low confidence - flag for user review
                result.requires_user_review = True
                self.stats['tracks_requiring_review'] += 1
                if result.is_arabic_track:
                    logger.warning(f"   ⚠️ [ARABIC] Low confidence match - REQUIRES USER REVIEW")
                    logger.warning(f"      Anghami: '{anghami_track.title}' by {anghami_track.primary_artist}")
                    logger.warning(f"      Spotify: '{result.best_match.title}' by {result.best_match.primary_artist}")
                    logger.warning(f"      Confidence: {confidence:.2f}")
                    logger.warning(f"      Strategies tried: {len(result.search_queries_tried)}")
                    if result.arabic_artist_variants_tried:
                        logger.warning(f"      Artist variants: {', '.join(result.arabic_artist_variants_tried)}")
                else:
                    logger.warning(f"   ⚠️ Low confidence match: {confidence:.2f}")
        else:
            result.requires_user_review = True
            self.stats['tracks_requiring_review'] += 1
            if result.is_arabic_track:
                logger.warning(f"   ❌ [ARABIC] No matches found for '{anghami_track.title}' - REQUIRES USER REVIEW")
                logger.warning(f"      Strategies tried: {len(result.search_queries_tried)}")
                if result.arabic_artist_variants_tried:
                    logger.warning(f"      Artist variants tried: {', '.join(result.arabic_artist_variants_tried)}")
            else:
                logger.warning(f"   ❌ No matches found for '{anghami_track.title}'")
            result.requires_user_review = True
    
    async def match_playlist(self, anghami_playlist: AnghamiPlaylist) -> List[MatchResult]:
        """Match all tracks in an Anghami playlist"""
        logger.info(f"🎵 Matching playlist: '{anghami_playlist.name}' ({len(anghami_playlist.tracks)} tracks)")
        
        results = []
        
        for i, track in enumerate(anghami_playlist.tracks, 1):
            logger.info(f"📀 Processing track {i}/{len(anghami_playlist.tracks)}")
            
            result = await self.match_track(track)
            results.append(result)
            
            # Progress update every 10 tracks
            if i % 10 == 0:
                successful = sum(1 for r in results if r.has_match)
                confident = sum(1 for r in results if r.has_confident_match)
                logger.info(f"   📊 Progress: {i}/{len(anghami_playlist.tracks)} - "
                          f"Found: {successful}, Confident: {confident}")
            
            # Small delay between tracks to respect rate limits
            await asyncio.sleep(0.1)
        
        # Final statistics
        successful = sum(1 for r in results if r.has_match)
        confident = sum(1 for r in results if r.has_confident_match)
        arabic_tracks = sum(1 for r in results if r.is_arabic_track)
        arabic_matched = sum(1 for r in results if r.is_arabic_track and r.has_match)
        arabic_confident = sum(1 for r in results if r.is_arabic_track and r.has_confident_match)
        requires_review = sum(1 for r in results if r.requires_user_review)
        
        logger.info(f"🏁 Playlist matching complete!")
        logger.info(f"   📊 Total matches: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
        logger.info(f"   🎯 Confident matches: {confident}/{len(results)} ({confident/len(results)*100:.1f}%)")
        
        if arabic_tracks > 0:
            logger.info(f"   🌍 Arabic tracks: {arabic_tracks}/{len(results)} ({arabic_tracks/len(results)*100:.1f}%)")
            logger.info(f"   🎭 Arabic matched: {arabic_matched}/{arabic_tracks} ({arabic_matched/arabic_tracks*100:.1f}%)")
            logger.info(f"   🏆 Arabic confident: {arabic_confident}/{arabic_tracks} ({arabic_confident/arabic_tracks*100:.1f}%)")
        
        if requires_review > 0:
            logger.warning(f"   ⚠️ Requires user review: {requires_review}/{len(results)} ({requires_review/len(results)*100:.1f}%)")
        
        return results
    
    def _generate_search_strategies(self, track: AnghamiTrack) -> List[Tuple[str, str]]:
        """Generate multiple search strategies for a track"""
        strategies = []
        
        if not track.title or not track.primary_artist:
            return strategies
        
        # Strategy 1: Exact field-specific search
        exact_query = f'track:"{track.title}" artist:"{track.primary_artist}"'
        strategies.append(("exact_fields", exact_query))
        
        # Strategy 2: Simple exact search
        simple_exact = f'"{track.title}" "{track.primary_artist}"'
        strategies.append(("exact_quoted", simple_exact))
        
        # Strategy 3: Normalized search (clean text)
        clean_title = self.normalizer.clean_search_text(track.title)
        clean_artist = self.normalizer.clean_search_text(track.primary_artist)
        if clean_title and clean_artist:
            normalized_query = f'track:"{clean_title}" artist:"{clean_artist}"'
            strategies.append(("normalized_fields", normalized_query))
        
        # Strategy 4: Main title only (remove featured artists)
        main_title = self.normalizer.extract_main_title(track.title)
        if main_title != track.title and main_title:
            main_title_query = f'track:"{main_title}" artist:"{track.primary_artist}"'
            strategies.append(("main_title", main_title_query))
        
        # Strategy 5: Broad search without field specifications
        broad_query = f"{clean_title} {clean_artist}"
        strategies.append(("broad_search", broad_query))
        
        # Strategy 6: Artist-only search (for very unclear titles)
        if len(clean_title) < 3:  # Very short or unclear title
            artist_query = f'artist:"{clean_artist}"'
            strategies.append(("artist_only", artist_query))
        
        # Strategy 7: Fallback - just the title
        if len(clean_title) > 3:
            title_only_query = f'track:"{clean_title}"'
            strategies.append(("title_only", title_only_query))
        
        return strategies
    
    async def _search_spotify(self, query: str, strategy: str) -> List[Dict]:
        """Search Spotify API with caching and rate limiting"""
        if not query.strip():
            return []
        
        # Check cache first
        cached_result = self.cache.get(query)
        if cached_result:
            self.stats['cache_hits'] += 1
            logger.debug(f"   💾 Cache hit for: {query}")
            return cached_result
        
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_delay:
            await asyncio.sleep(self.request_delay - elapsed)
        
        try:
            # Make API request
            self.last_request_time = time.time()
            response = self.spotify_auth.make_authenticated_request(
                'GET',
                'https://api.spotify.com/v1/search',
                params={
                    'q': query,
                    'type': 'track',
                    'limit': self.max_search_results,
                    'market': 'US'  # Can be configured
                }
            )
            
            self.stats['api_calls'] += 1
            
            search_data = response.json()
            tracks = search_data.get('tracks', {}).get('items', [])
            
            # Cache the result
            self.cache.set(query, tracks)
            
            logger.debug(f"   🌐 API call for: {query} - Found {len(tracks)} results")
            return tracks
            
        except Exception as e:
            logger.error(f"   💥 Spotify search failed: {e}")
            return []
    
    def _score_matches(self, anghami_track: AnghamiTrack, spotify_tracks: List[Dict], strategy: str) -> List[SpotifyTrackMatch]:
        """Score and convert Spotify API results to SpotifyTrackMatch objects"""
        matches = []
        
        for spotify_track in spotify_tracks:
            try:
                # Extract track data
                title = spotify_track.get('name', '')
                artists = [artist.get('name', '') for artist in spotify_track.get('artists', [])]
                album = spotify_track.get('album', {}).get('name', '')
                
                # Calculate confidence score
                confidence, reasons = self._calculate_confidence(anghami_track, title, artists, album)
                
                # Create match object
                match = SpotifyTrackMatch(
                    spotify_id=spotify_track.get('id', ''),
                    title=title,
                    artists=artists,
                    album=album,
                    duration_ms=spotify_track.get('duration_ms', 0),
                    preview_url=spotify_track.get('preview_url'),
                    external_urls=spotify_track.get('external_urls', {}),
                    confidence_score=confidence,
                    match_strategy=strategy,
                    match_reasons=reasons
                )
                
                matches.append(match)
                
            except Exception as e:
                logger.warning(f"   ⚠️ Error processing Spotify track: {e}")
                continue
        
        # Sort by confidence score (highest first)
        matches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return matches
    
    def _calculate_confidence(self, anghami_track: AnghamiTrack, spotify_title: str, spotify_artists: List[str], spotify_album: str) -> Tuple[float, List[str]]:
        """Calculate confidence score for a potential match with Arabic-aware scoring"""
        reasons = []
        score_components = []
        
        # Check if this is an Arabic track for adjusted scoring
        is_arabic = (
            self.arabic_transliterator.is_arabic_text(anghami_track.title) or
            any(self.arabic_transliterator.is_arabic_text(artist) for artist in anghami_track.artists)
        )
        
        # Title similarity with Arabic awareness
        if is_arabic:
            # For Arabic tracks, use both regular and transliteration-aware matching
            regular_similarity = self.normalizer.similarity_score(anghami_track.title, spotify_title)
            
            # Try transliteration variants for Arabic titles
            title_variants = self.arabic_transliterator.get_transliteration_variants(anghami_track.title)
            transliteration_similarity = 0.0
            
            for variant in title_variants:
                variant_similarity = self.normalizer.similarity_score(variant, spotify_title)
                transliteration_similarity = max(transliteration_similarity, variant_similarity)
            
            title_similarity = max(regular_similarity, transliteration_similarity)
            
            if transliteration_similarity > regular_similarity:
                reasons.append("Arabic transliteration title match")
            
        else:
            title_similarity = self.normalizer.similarity_score(anghami_track.title, spotify_title)
        
        # Weight adjustment for Arabic tracks (lower title weight, higher artist weight)
        title_weight = 0.4 if is_arabic else 0.5
        artist_weight = 0.5 if is_arabic else 0.4
        
        score_components.append(title_similarity * title_weight)
        
        if title_similarity > 0.9:
            reasons.append("Excellent title match")
        elif title_similarity > 0.7:
            reasons.append("Good title match")
        elif title_similarity > 0.5:
            reasons.append("Partial title match")
        
        # Artist similarity with Arabic transliteration support
        best_artist_similarity = 0.0
        best_artist_match = ""
        
        if anghami_track.artists and spotify_artists:
            for anghami_artist in anghami_track.artists:
                for spotify_artist in spotify_artists:
                    if is_arabic and self.arabic_transliterator.is_arabic_text(anghami_artist):
                        # Use Arabic-aware matching
                        similarity = self.arabic_transliterator._phonetic_similarity(anghami_artist, spotify_artist)
                        
                        # Also try regular similarity as fallback
                        regular_similarity = self.normalizer.similarity_score(anghami_artist, spotify_artist)
                        similarity = max(similarity, regular_similarity)
                        
                    else:
                        # Regular similarity for non-Arabic artists
                        similarity = self.normalizer.similarity_score(anghami_artist, spotify_artist)
                    
                    if similarity > best_artist_similarity:
                        best_artist_similarity = similarity
                        best_artist_match = spotify_artist
        
        score_components.append(best_artist_similarity * artist_weight)
        
        if best_artist_similarity > 0.9:
            reasons.append(f"Excellent artist match: {best_artist_match}")
        elif best_artist_similarity > 0.7:
            reasons.append(f"Good artist match: {best_artist_match}")
        elif best_artist_similarity > 0.5:
            reasons.append(f"Partial artist match: {best_artist_match}")
        
        # Arabic-specific bonuses
        if is_arabic:
            # Bonus for finding any reasonable artist match (Arabic is harder)
            if best_artist_similarity > 0.6:
                score_components.append(0.1)
                reasons.append("Arabic artist successfully identified")
            
            # Bonus for discography matches
            if any("discography" in reason for reason in reasons):
                score_components.append(0.1)
                reasons.append("Found via artist discography search")
        
        # Regular bonuses
        if title_similarity == 1.0:
            score_components.append(0.05)
            reasons.append("Exact title match")
        
        if best_artist_similarity == 1.0:
            score_components.append(0.05)
            reasons.append("Exact artist match")
        
        # Calculate final score
        final_score = min(sum(score_components), 1.0)
        
        # Arabic tracks get adjusted threshold consideration
        if is_arabic and final_score > 0.5:
            reasons.append("Arabic track with reasonable confidence")
        
        return final_score, reasons
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get matching statistics"""
        cache_stats = self.cache.get_stats()
        
        return {
            'search_stats': self.stats,
            'cache_stats': cache_stats,
            'configuration': {
                'confidence_threshold': self.confidence_threshold,
                'max_search_results': self.max_search_results,
                'request_delay': self.request_delay
            }
        }
    
    def save_results(self, results: List[MatchResult], output_file: Path) -> None:
        """Save matching results to JSON file"""
        try:
            # Convert to serializable format
            serializable_results = [result.to_dict() for result in results]
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'matching_session': {
                        'timestamp': datetime.now().isoformat(),
                        'total_tracks': len(results),
                        'successful_matches': sum(1 for r in results if r.has_match),
                        'confident_matches': sum(1 for r in results if r.has_confident_match),
                        'statistics': self.get_statistics()
                    },
                    'results': serializable_results
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Matching results saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")


async def main():
    """Test the Spotify track matching engine"""
    import sys
    
    # Create matcher
    matcher = SpotifyTrackMatcher()
    
    print("🎯 Spotify Track Matching Engine - Test Mode")
    print("=" * 60)
    
    # Authenticate
    if not matcher.authenticate():
        print("❌ Authentication failed")
        return
    
    # Test with sample data
    if len(sys.argv) > 1:
        playlist_file = Path(sys.argv[1])
        if playlist_file.exists():
            try:
                with open(playlist_file, 'r', encoding='utf-8') as f:
                    playlist_data = json.load(f)
                
                # Convert to AnghamiPlaylist
                anghami_playlist = AnghamiPlaylist.from_dict(playlist_data)
                
                print(f"🎵 Testing with playlist: {anghami_playlist.name}")
                print(f"📀 Total tracks: {len(anghami_playlist.tracks)}")
                
                # Match tracks
                results = await matcher.match_playlist(anghami_playlist)
                
                # Show results
                print(f"\n📊 MATCHING RESULTS:")
                print(f"Total tracks: {len(results)}")
                print(f"Successful matches: {sum(1 for r in results if r.has_match)}")
                print(f"High confidence: {sum(1 for r in results if r.has_confident_match)}")
                
                # Save results
                output_file = Path(f"data/matching_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                matcher.save_results(results, output_file)
                
            except Exception as e:
                print(f"❌ Error processing playlist: {e}")
        else:
            print(f"❌ Playlist file not found: {playlist_file}")
    else:
        # Test with a single track
        test_track = AnghamiTrack(
            title="Pink + White",
            artists=["Frank Ocean"]
        )
        
        print(f"🔍 Testing with single track: '{test_track.title}' by {test_track.primary_artist}")
        
        result = await matcher.match_track(test_track)
        
        if result.has_match:
            print(f"✅ Match found: '{result.best_match.title}' by {result.best_match.primary_artist}")
            print(f"🎯 Confidence: {result.best_match.confidence_score:.2f}")
            print(f"🔗 Spotify URL: {result.best_match.spotify_url}")
        else:
            print("❌ No match found")
    
    # Show statistics
    stats = matcher.get_statistics()
    print(f"\n📈 STATISTICS:")
    for key, value in stats['search_stats'].items():
        print(f"   {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main()) 