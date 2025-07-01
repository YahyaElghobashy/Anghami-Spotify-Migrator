# 🚀 Anghami-Spotify Migration Tool - Commands Cheatsheet

*Quick reference for all available commands and shortcuts*

## ⚡ Quick Access Commands

### Essential Shortcuts
```bash
./upcom         # Show most used and recent commands
./excom         # Show all commands categorized with full details
```

### Python CLI Commands
```bash
python3 cli.py upcom           # Same as ./upcom
python3 cli.py excom           # Same as ./excom
python3 cli.py quick-show      # Show most used commands only
python3 cli.py quick-commands  # Export commands for Cursor
```

---

## 🏗️ Project Setup & Development

### Initial Setup
```bash
python3 cli.py setup           # Set up project environment
python3 cli.py clean-install   # Clean install all dependencies
```

### Development Servers
```bash
python3 cli.py start-backend   # Start FastAPI backend (port 8000)
python3 cli.py start-frontend  # Start React frontend (port 5173)
python3 cli.py start-dev       # Start both servers together
./test_integration.sh          # Start full development environment
```

### Building & Production
```bash
python3 cli.py build           # Build frontend for production
cd ui && npm run build         # Direct frontend build
```

---

## 🧪 Testing & Validation

### Integration Testing
```bash
./test.sh                      # Run comprehensive test suite
./test.sh -d                   # Run tests with UI (debug mode)
./test.sh -b firefox           # Run tests in specific browser
./test.sh -p mobile-chrome     # Run mobile tests
```

### Backend Testing
```bash
python3 cli.py test-backend    # Test all API endpoints
python3 cli.py check-integration  # Check if services are running
curl -s http://localhost:8000/health  # Direct health check
```

### Migration Testing
```bash
python3 cli.py test-migration  # Test playlist migration flow
```

---

## 📊 Data Management

### Playlist Extraction
```bash
python3 cli.py extract <playlist-id>      # Extract specific playlist
python3 src/extractors/anghami_direct_extractor.py <url>  # Direct extraction
```

### Logs & Monitoring
```bash
python3 cli.py logs                # View both backend and frontend logs
python3 cli.py logs backend        # Backend logs only
python3 cli.py logs frontend       # Frontend logs only
tail -f backend.log                # Live backend log monitoring
tail -f frontend.log               # Live frontend log monitoring
```

### Data Cleanup
```bash
python3 cli.py clean-data          # Clean temporary data and logs
rm -rf data/temp/*                 # Manual temp cleanup
```

---

## 🛠️ System Utilities

### Process Management
```bash
python3 cli.py kill-servers        # Kill all running servers
python3 cli.py ports               # Show port usage (3000, 8000)
lsof -i :3000,8000                 # Direct port check
```

### System Status
```bash
python3 cli.py status              # Complete project health check
python3 cli.py stats               # Command usage statistics
git status                         # Git repository status
```

---

## 📋 Command History & Analytics

### Usage Tracking
```bash
python3 cli.py stats               # Show command usage statistics
python3 cli.py quick-show          # Most used commands
./upcom                            # Quick commands with recent history
```

### Command Categories (via ./excom)
- **🚀 Project Setup**: setup, clean-install
- **🔧 Development**: start-backend, start-frontend, start-dev, build
- **🧪 Testing**: test-backend, test-migration, check-integration
- **📊 Data Management**: extract, logs, clean-data
- **🛠️ Utilities**: ports, kill-servers, status, stats
- **📋 Quick Access**: upcom, excom, quick-show, quick-commands

---

## 🎯 Common Workflows

### Daily Development
```bash
./upcom                            # Check recent commands
python3 cli.py start-dev           # Start development environment
python3 cli.py status              # Check everything is running
./test.sh                          # Run tests before committing
```

### Debugging Issues
```bash
python3 cli.py kill-servers        # Stop all services
python3 cli.py clean-data          # Clean temporary data
python3 cli.py check-integration   # Verify services
python3 cli.py logs                # Check logs for errors
```

### Testing & Quality Assurance
```bash
./test.sh -d                       # Debug mode testing
./test.sh -p mobile-chrome         # Mobile testing
python3 cli.py test-migration      # Migration testing
python3 cli.py build               # Production build test
```

### Data Extraction
```bash
python3 cli.py extract 276644689   # Extract playlist by ID
python3 cli.py logs backend        # Monitor extraction logs
ls -la data/playlists/             # Check extracted data
```

---

## 💡 Pro Tips

- **Command History**: All commands are tracked in `~/.anghami-spotify-cli/`
- **Quick Access**: Use `./upcom` for instant command reference
- **Comprehensive Help**: Use `./excom` for categorized command list
- **Live Monitoring**: Use `tail -f *.log` for real-time debugging
- **Git Integration**: All commands work with the clean repository structure
- **Cross-Platform**: All commands work on macOS, Linux, and Windows (with appropriate shell)

---

## 📈 Statistics & Monitoring

The CLI tracks:
- ✅ **Command Usage Count**: How often each command is used
- ✅ **Recent History**: Last 50 commands with timestamps
- ✅ **Success Rates**: Command execution success tracking
- ✅ **Performance**: Command execution timing

Access via:
- `python3 cli.py stats` - Full statistics
- `./upcom` - Quick recent commands
- `./excom` - Complete categorized view

---

**Repository**: https://github.com/YahyaElghobashy/Anghami-Spotify-Migrator  
**Status**: ✅ All systems operational and fully tested!

*Last updated: 2025-07-01* 