# TuneMyMusic Automation Script

## Overview

The TuneMyMusic Automation Script provides a complete solution for migrating Anghami playlists to Spotify using TuneMyMusic.com as an intermediary service. Instead of implementing our own track matching and Spotify integration, this script automates the TuneMyMusic web interface to leverage their superior matching algorithms and direct Spotify integration.

## Key Features

- **Batch Processing**: Migrate multiple playlists in one session
- **Duplicate Prevention**: Automatically skips already processed playlists  
- **Complete Workflow**: Handles the entire transfer process automatically
- **CSV Export**: Downloads unmigrated tracks as CSV files
- **Session Tracking**: Maintains detailed logs and statistics
- **Error Recovery**: Takes screenshots and logs errors for debugging
- **Progress Persistence**: Can resume interrupted sessions

## How It Works

The automation script follows this workflow for each playlist:

1. 🌐 **Navigate to TuneMyMusic** - Loads the transfer page
2. 🎵 **Select Anghami Source** - Chooses Anghami as the source platform
3. 🔗 **Input Playlist URL** - Enters the Anghami playlist URL
4. 📥 **Load Playlist Data** - Waits for the playlist to load completely
5. 🎯 **Select Spotify Destination** - Chooses Spotify as the target
6. ⚙️ **Configure Settings** - Selects all tracks for transfer
7. 🚀 **Start Transfer** - Initiates the migration process
8. ⏳ **Wait for Completion** - Monitors transfer progress
9. 📄 **Download CSV** - Saves unmigrated tracks if available
10. 📸 **Take Screenshots** - Captures final state for verification

## Usage

### Command Line

```bash
# Single playlist
python src/extractors/tunemymusic_automation.py "https://play.anghami.com/playlist/12345"

# Multiple playlists
python src/extractors/tunemymusic_automation.py \
  "https://play.anghami.com/playlist/12345" \
  "https://play.anghami.com/playlist/67890" \
  "https://play.anghami.com/playlist/11111"

# Interactive mode (no arguments)
python src/extractors/tunemymusic_automation.py
```

### Programmatic Usage

```python
import asyncio
from src.extractors.tunemymusic_automation import TuneMyMusicAutomation

async def migrate_my_playlists():
    automation = TuneMyMusicAutomation()
    
    playlist_urls = [
        "https://play.anghami.com/playlist/12345",
        "https://play.anghami.com/playlist/67890",
        "https://play.anghami.com/playlist/11111"
    ]
    
    results = await automation.migrate_playlists(playlist_urls)
    print(f"Migration completed: {results}")

# Run the migration
asyncio.run(migrate_my_playlists())
```

## Configuration

The script uses the centralized configuration system. Key settings:

```python
# In src/utils/config.py

@dataclass
class TuneMyMusicConfig:
    base_url: str = "https://www.tunemymusic.com"
    transfer_url: str = "https://www.tunemymusic.com/transfer"
    
    # Selectors (automatically updated if TuneMyMusic changes)
    anghami_button_selector: str = 'button[data-id="3"]'
    url_input_selector: str = 'input[placeholder*="playlist"]'
    load_button_selector: str = 'button:has-text("Load my music")'
    
    # Timeouts
    navigation_timeout: int = 30000
    load_timeout: int = 60000
```

## Output Files

The automation generates several output files:

### Session Logs
- `data/logs/migration_session_YYYYMMDD_HHMMSS.log` - Detailed session log
- `data/logs/processed_playlists.json` - List of completed playlists
- `data/logs/migration_report_YYYYMMDD_HHMMSS.txt` - Final summary report

### Screenshots
- `data/screenshots/playlist_ID_loaded.png` - Playlist loaded in TuneMyMusic
- `data/screenshots/playlist_ID_completed.png` - Transfer completion screen
- `data/screenshots/playlist_ID_error.png` - Error screenshots (if any)

### CSV Files
- `data/unmigrated_tracks/unmigrated_tracks_ID_SESSION.csv` - Tracks that couldn't be migrated

## Example Session Output

```
🎵 TuneMyMusic Automation - Anghami to Spotify Migration
============================================================

🚀 Starting migration of 3 playlists...

📀 Processing playlist 1/3: https://play.anghami.com/playlist/12345
�� Loading TuneMyMusic...
🎵 Selecting Anghami as source...
🔗 Entering playlist URL...
📥 Loading playlist data...
✅ Playlist loaded with 45 tracks
🎯 Selecting Spotify as destination...
⚙️ Configuring transfer settings...
🚀 Starting transfer to Spotify...
⏳ Waiting for transfer completion...
✅ Transfer completed!
📄 Checking for unmigrated tracks...
✅ Downloaded unmigrated tracks CSV: data/unmigrated_tracks/unmigrated_tracks_12345_20250101_143022.csv
✅ Successfully migrated playlist 1

⏸️  Waiting 30 seconds before next playlist...

[Process repeats for remaining playlists...]

🎉 TuneMyMusic Migration Session Complete!

📊 SESSION STATISTICS:
==================================================
Total Playlists: 3
✅ Successful Transfers: 3
❌ Failed Transfers: 0
⏭️ Skipped Duplicates: 0

🎵 TRACK STATISTICS:
==================================================
Total Tracks Migrated: 127
Total Tracks Unmigrated: 8
Success Rate: 94.1%
```

## Error Handling

The script includes comprehensive error handling:

- **Network Issues**: Automatic retries and timeouts
- **Element Not Found**: Multiple selector strategies
- **Transfer Failures**: Screenshots and detailed error logs
- **Interrupted Sessions**: Can resume from processed_playlists.json

## Duplicate Prevention

The script maintains a persistent record of processed playlists in `data/logs/processed_playlists.json`. When running the script multiple times:

- ✅ **Already Processed**: Skips playlists that were successfully migrated
- 🔄 **Retry Failed**: Re-attempts playlists that previously failed
- 📊 **Statistics**: Tracks skipped duplicates in the final report

## Benefits Over Custom Implementation

Using TuneMyMusic automation provides several advantages:

1. **Superior Matching**: TuneMyMusic has sophisticated algorithms for track matching
2. **Spotify Integration**: Direct integration eliminates complex OAuth setup
3. **Maintained Service**: TuneMyMusic handles API changes and updates
4. **Unmigrated Tracking**: Built-in CSV export for tracks that couldn't be found
5. **Faster Development**: No need to implement Phase 3+ ourselves

## Troubleshooting

### Common Issues

**Playlist Not Loading**
- Check that the Anghami playlist URL is public
- Verify the playlist still exists
- Look at the loading screenshot for clues

**Transfer Fails**
- Ensure Spotify account is connected to TuneMyMusic
- Check for TuneMyMusic service status
- Review error screenshots

**Selector Not Found**
- TuneMyMusic may have updated their interface
- Update selectors in config.py
- Check browser console for element IDs

### Debug Mode

Set `headless: false` in config to watch the automation in action:

```python
# In src/utils/config.py
@dataclass
class ExtractorConfig:
    headless: bool = False  # Set to False for debugging
```

## Next Steps

With this automation script, you have effectively completed the migration tool! The script:

- ✅ **Phase 1**: Spotify authentication (handled by TuneMyMusic)
- ✅ **Phase 2**: Anghami extraction (loads playlists in TuneMyMusic)  
- ✅ **Phase 3**: Track matching (TuneMyMusic's algorithms)
- ✅ **Phase 4**: Spotify creation (TuneMyMusic's integration)
- ✅ **Phase 5**: Batch processing and reporting

You can now migrate entire Anghami libraries to Spotify efficiently!
