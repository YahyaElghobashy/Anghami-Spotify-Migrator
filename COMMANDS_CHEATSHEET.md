# 🚀 Anghami-Spotify Migration Tool - Commands Cheatsheet

*Quick reference for all available commands and shortcuts*

## ⚡ Quick Access Commands

### Essential Shortcuts
```bash
./upcom         # Show most essential development commands
./excom         # Show complete command reference with categories
```

### Python CLI Commands
```bash
python3 cli.py upcom           # Show quick commands via CLI
python3 cli.py excom           # Show all commands via CLI
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
python3 cli.py start-backend   # Start modular backend (port 8000)
python3 cli.py start-frontend  # Start React frontend (port 5173)
python3 cli.py start-both      # Start both servers in parallel ⭐ MOST USED
python3 cli.py start-dev       # Start full development environment
./test_integration.sh          # Alternative full development startup
```

### Building & Production
```bash
python3 cli.py build           # Build frontend for production
cd ui && npm run build         # Direct frontend build
```

---

## 🧪 Testing & Validation

### Comprehensive Testing
```bash
./test.sh                      # Run full integration test suite ⭐ RECOMMENDED
python3 cli.py test-integration # Run comprehensive integration tests
python3 cli.py test-backend    # Test backend API endpoints specifically
python3 cli.py test-frontend   # Test frontend application
python3 cli.py check-integration # Quick service status check
```

### Backend Testing
```bash
python3 cli.py test-backend    # Test all API endpoints with JSON output
curl -s http://localhost:8000/health | jq .  # Direct health check
curl -s http://localhost:8000/profiles/history # Test profiles endpoint
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
python3 cli.py kill-servers        # Kill all running servers ⭐ ESSENTIAL
python3 cli.py ports               # Show port usage (5173, 8000)
lsof -i :5173,8000                 # Direct port check
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
./upcom                            # Essential commands with workflow
```

### Command Categories (via ./excom)
- **🔧 Development**: start-backend, start-frontend, start-both, build
- **🧪 Testing**: test-backend, test-frontend, test-integration, check-integration
- **🛠️ Utilities**: kill-servers, ports, status, clean-data
- **📊 Data Management**: extract, logs, stats
- **🚀 Setup**: setup, clean-install
- **📋 Quick Access**: upcom, excom, quick-show, quick-commands

---

## 🎯 Common Workflows

### Daily Development ⭐ RECOMMENDED WORKFLOW
```bash
./upcom                            # Check essential commands
python3 cli.py start-both          # Start both servers
python3 cli.py check-integration   # Verify everything is running
# ... do development work ...
python3 cli.py kill-servers        # Clean shutdown
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
./test.sh                          # Comprehensive testing ⭐ PRIMARY
python3 cli.py test-backend        # Backend-specific testing
python3 cli.py test-frontend       # Frontend-specific testing
python3 cli.py test-migration      # Migration testing
python3 cli.py build               # Production build test
```

### Data Extraction & Migration
```bash
python3 cli.py extract 276644689   # Extract playlist by ID
python3 cli.py logs backend        # Monitor extraction logs
ls -la data/playlists/             # Check extracted data
python3 cli.py test-migration      # Test migration process
```

---

## 💡 Pro Tips

- **⚡ Quick Start**: Use `python3 cli.py start-both` for fastest development setup
- **🧪 Quick Test**: Use `python3 cli.py check-integration` to verify services
- **🛑 Clean Stop**: Always use `python3 cli.py kill-servers` for clean shutdown
- **📋 Command Discovery**: Use `./upcom` for essentials, `./excom` for complete reference
- **🔍 Live Monitoring**: Use `tail -f *.log` for real-time debugging
- **📊 Port Management**: Frontend runs on 5173, Backend on 8000
- **🏗️ Modular Backend**: Backend now uses `python3 -m backend.main` structure
- **📈 Usage Tracking**: All commands tracked in `~/.anghami-spotify-cli/`

---

## 📈 Statistics & Monitoring

The CLI tracks:
- ✅ **Command Usage Count**: How often each command is used
- ✅ **Recent History**: Last 50 commands with timestamps
- ✅ **Success Rates**: Command execution success tracking
- ✅ **Performance**: Command execution timing

Access via:
- `python3 cli.py stats` - Full statistics
- `./upcom` - Essential commands and workflow
- `./excom` - Complete categorized view

---

**Repository**: https://github.com/YahyaElghobashy/Anghami-Spotify-Migrator  
**Status**: ✅ Modular backend architecture - All systems operational!

*Last updated: 2025-07-01* 