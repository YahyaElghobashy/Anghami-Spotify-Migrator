# Anghami Playlist Extractors Usage Guide

## Overview

You now have two powerful methods to extract playlist data from Anghami:

1. **Direct Anghami Extractor** (`anghami_direct_extractor.py`)
2. **TuneMyMusic Proxy Extractor** (`tunemymusic_proxy_extractor.py`)

## Quick Start

### Test Both Methods
```bash
python test_both_extractors.py
```

This will test both extractors with your "Experimental 2.0" playlist and show you which method works best.

### Run Individual Extractors

#### Direct Anghami Method
```bash
python anghami_direct_extractor.py
```

#### TuneMyMusic Proxy Method  
```bash
python tunemymusic_proxy_extractor.py
```

## Method Comparison

| Feature | Direct Anghami | TuneMyMusic Proxy |
|---------|---------------|-------------------|
| **Speed** | ⚡ Fast | 🐌 Slower (loads external site) |
| **Reliability** | ⚠️ May be blocked by anti-bot | ✅ More reliable |
| **Metadata** | 📝 Full metadata + cover art | 📝 Basic metadata |
| **Track Extraction** | 🎵 Direct from Anghami | 🎵 Via TuneMyMusic parsing |
| **Dependencies** | Playwright only | Playwright only |

## What Each Extractor Does

### Direct Anghami Extractor
1. 🌐 Loads the Anghami playlist page directly
2. 📸 Takes screenshot (`anghami_loaded.png`)
3. 🔍 Extracts playlist metadata (name, description, creator)
4. 🖼️ Downloads cover art automatically
5. 🎵 Extracts all track names and artists
6. 💾 Saves to `extracted_playlists/playlist_ID_direct.json`

### TuneMyMusic Proxy Extractor
1. 🌐 Navigates to TuneMyMusic.com
2. 🎵 Selects Anghami as source platform
3. 📋 Inputs your playlist URL
4. ⏳ Waits for TuneMyMusic to load the playlist
5. 📸 Takes screenshot (`tunemymusic_loaded.png`)
6. 🎵 Extracts tracks using TuneMyMusic's parsed structure
7. 💾 Saves to `extracted_playlists/playlist_ID_tunemymusic.json`

## Output Files

Both extractors create:
- `📁 extracted_playlists/` folder
- `📄 playlist_XXXXXX_[method].json` - Complete playlist data
- `📸 Screenshot files` for debugging
- `🖼️ cover_art_XXXXXX.jpg` (direct method only)

## Troubleshooting

### If Direct Method Fails:
- ✅ Use TuneMyMusic proxy instead
- 🔄 Try running again (timing issues)
- 🌐 Check internet connection

### If TuneMyMusic Method Fails:
- 🔄 Try running again
- 🌐 Check if TuneMyMusic.com is accessible
- ⏱️ Wait longer for content to load

### If Both Methods Fail:
- ✅ Verify playlist URL is correct
- 🔓 Check if playlist is public
- 🌐 Test network connectivity

## Integration with Migration

Once extraction works, the playlist data will be ready for **Phase 3** (Spotify migration):

```json
{
  "id": "276644689",
  "name": "Experimental 2.0",
  "tracks": [
    {
      "name": "Billie Bossa Nova",
      "artist": "Billie Eilish",
      "position": 1
    }
  ]
}
```

## Expected Results

For your "Experimental 2.0" playlist, you should see:
- ✅ **126 tracks** extracted
- 🎵 Artists like: Billie Eilish, The Weeknd, Lana Del Rey, d4vd
- 📀 Playlist name: "Experimental 2.0"
- 🖼️ Cover art downloaded (direct method)

Success! 🎉 