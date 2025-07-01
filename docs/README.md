# 🎵 Anghami to Spotify Migration Tool - Phase 1 & 2

A comprehensive tool for migrating playlists from Anghami to Spotify with full metadata preservation.

## 📋 Current Implementation Status

### ✅ Phase 1: Authentication & Credentials Management (COMPLETE)
- **Spotify OAuth2 Authentication** - Full Authorization Code Flow implementation
- **Token Management** - Automatic refresh and secure storage
- **Rate Limiting** - Handles Spotify API limits with retry logic
- **Error Handling** - Comprehensive error recovery and user feedback

### ✅ Phase 2: Anghami Data Retrieval Engine (COMPLETE)
- **Profile Extraction** - Extract user profile information
- **Playlist Discovery** - Find all user-created playlists
- **Track Metadata** - Extract track details with artist, album, duration
- **Cover Art URLs** - Extract playlist and track cover art
- **Data Models** - Structured data classes for all entities

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your Spotify credentials:

```env
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

**Getting Spotify Credentials:**
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app
3. Add `http://localhost:8888/callback` to Redirect URIs
4. Copy Client ID and Client Secret to your `.env` file

### 3. Testing Phase 1 - Spotify Authentication

```bash
# Test complete authentication system
python test_spotify_auth.py

# Test specific components
python test_spotify_auth.py --test-auth
python test_spotify_auth.py --test-playlist-creation
python test_spotify_auth.py --test-cover-upload
```

### 4. Testing Phase 2 - Anghami Extraction

```bash
# Test with a real Anghami profile
python test_anghami_extraction.py --profile-url "https://anghami.com/user/username"

# Test metadata parsing only
python test_anghami_extraction.py --validate-metadata
```

## 📁 Project Structure

```
anghami-spotify-migrator/
├── 📄 anghami_models.py          # Data models for playlists/tracks
├── 📄 spotify_auth.py            # Spotify OAuth2 authentication
├── 📄 anghami_extractor.py       # Anghami data extraction
├── 📄 test_spotify_auth.py       # Spotify authentication tests
├── 📄 test_anghami_extraction.py # Anghami extraction tests
├── 📄 config.json               # Configuration settings
├── 📄 requirements.txt          # Python dependencies
└── 📄 README.md                 # This file
```

## 🔧 API Documentation

### Spotify Authentication

```python
from spotify_auth import create_spotify_auth

# Create authenticated Spotify client
auth = create_spotify_auth()

# Authenticate (opens browser)
if auth.authenticate():
    # Make authenticated requests
    response = auth.make_authenticated_request('GET', 'https://api.spotify.com/v1/me')
    user_data = response.json()
```

### Anghami Data Extraction

```python
from anghami_extractor import extract_anghami_profile

# Extract complete profile with all playlists
profile = extract_anghami_profile("https://anghami.com/user/username")

print(f"Found {profile.total_playlists} playlists")
print(f"Total tracks: {profile.total_tracks}")

# Access playlists
for playlist in profile.playlists:
    print(f"Playlist: {playlist.name} ({playlist.track_count} tracks)")
    
    # Access tracks
    for track in playlist.tracks:
        print(f"  - {track.title} by {track.all_artists_string}")
        print(f"    Duration: {track.duration_formatted}")
```

### Data Models

```python
from anghami_models import AnghamiTrack, AnghamiPlaylist, AnghamiProfile

# Create track
track = AnghamiTrack(
    title="Song Title",
    artists=["Artist 1", "Artist 2"],
    album="Album Name",
    duration_seconds=240
)

# Generate Spotify search query
search_query = track.to_search_query()
# Output: track:"Song Title" artist:"Artist 1" album:"Album Name"

# Create playlist
playlist = AnghamiPlaylist(
    id="playlist_123",
    name="My Playlist",
    url="https://anghami.com/playlist/123"
)

# Add tracks
playlist.add_track(track)
print(f"Total duration: {playlist.total_duration_formatted}")
```

## 🧪 Testing Framework

### Spotify Authentication Tests

The test suite validates all authentication functionality:

- **OAuth2 Flow** - Complete browser-based authentication
- **API Requests** - Authenticated requests with error handling
- **Playlist Creation** - Test playlist management permissions
- **Cover Art Upload** - Image upload functionality
- **Rate Limiting** - Proper handling of API limits

### Anghami Extraction Tests

The test suite validates data extraction:

- **Profile Parsing** - Extract user information
- **Playlist Discovery** - Find all user playlists
- **Track Extraction** - Extract metadata from playlist pages
- **URL Handling** - Proper URL resolution and validation
- **Data Models** - Validate object creation and methods

## ⚙️ Configuration Options

### Spotify Settings
- **Client ID/Secret** - Your Spotify app credentials
- **Redirect URI** - OAuth callback URL (must match Spotify app settings)
- **Scopes** - Required permissions for playlist management

### Anghami Settings
- **User Agent** - Browser identification for web scraping
- **Request Delay** - Time between requests (respect rate limits)
- **Max Retries** - Number of retry attempts for failed requests

### Migration Settings
- **Batch Size** - Number of tracks to process at once
- **Search Limit** - Maximum Spotify search results per track
- **Confidence Threshold** - Minimum match confidence for track selection

## 🔍 Troubleshooting

### Spotify Authentication Issues

**Problem:** Browser doesn't open automatically
```bash
# Solution: Manual URL visit
# The script will print the authorization URL to visit manually
```

**Problem:** "Invalid redirect URI" error
```bash
# Solution: Check Spotify app settings
# Ensure http://localhost:8888/callback is added to Redirect URIs in your Spotify app
```

**Problem:** Token refresh failures
```bash
# Solution: Re-authenticate
# Delete any .spotify_tokens.json file and authenticate again
```

### Anghami Extraction Issues

**Problem:** No playlists found
```bash
# Solution: Check profile URL format
# Ensure URL is: https://anghami.com/user/username
# Make sure the profile is public
```

**Problem:** Empty track lists
```bash
# Solution: Check playlist accessibility
# Some playlists may be private or require authentication
# Try with public playlists first
```

**Problem:** Rate limiting errors
```bash
# Solution: Increase request delay
# Edit config.json and increase anghami.request_delay value
```

## 📊 Success Criteria

### Phase 1 (Authentication) - ✅ COMPLETE
- [x] Successful OAuth2 authentication with Spotify
- [x] Automatic token refresh functionality
- [x] Rate limiting with Retry-After header support
- [x] Playlist creation and management permissions
- [x] Cover art upload capability

### Phase 2 (Data Extraction) - ✅ COMPLETE
- [x] Extract user profile information from Anghami
- [x] Discover all user-created playlists
- [x] Extract complete track metadata (title, artists, album, duration)
- [x] Handle pagination for large playlists
- [x] Extract cover art URLs for playlists and tracks

## 🚧 Next Steps (Upcoming Phases)

### Phase 3: Interactive Playlist Selection UI
- Rich console interface for playlist selection
- Multi-select with search/filter functionality
- Preview and confirmation screens

### Phase 4: Spotify Playlist Creation Engine
- Create Spotify playlists with metadata
- Upload cover art to created playlists
- Interactive prompts for missing descriptions

### Phase 5: Advanced Track Matching & Migration
- Intelligent track search with fuzzy matching
- Confidence scoring for track matches
- Batch track addition to Spotify playlists

## 📞 Support

### Environment Variables
Make sure these are set in your `.env` file:
```env
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

### Common Commands
```bash
# Test everything
python test_spotify_auth.py && python test_anghami_extraction.py --validate-metadata

# Test with real data
python test_anghami_extraction.py --profile-url "https://anghami.com/user/YOUR_USERNAME"

# Debug authentication
python spotify_auth.py
```

### Dependencies
All required packages are in `requirements.txt`:
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `python-dotenv` - Environment variables
- `dataclasses-json` - Data model serialization

---

**⭐ This is a modular implementation following the phase-based development plan. Each phase can be tested and debugged independently before moving to the next.** 