# 🎵 Anghami → Spotify Migration Tool - CLI Documentation

## Overview

The CLI tool (`cli.py`) provides a comprehensive command-line interface for managing the Anghami to Spotify migration project. It includes command tracking, usage statistics, and easy integration with Cursor IDE.

## 🚀 Quick Start

```bash
# Make executable (first time only)
chmod +x cli.py

# Show all available commands
python3 cli.py

# Set up the project
python3 cli.py setup

# Start development environment
python3 cli.py start-dev
```

## 📋 Command Categories

### 🔧 Project Setup
- `setup` - Set up complete project environment
- `clean-install` - Clean installation of all dependencies

### 🚀 Development
- `start-backend` - Start backend API server only
- `start-frontend` - Start frontend dev server only
- `start-dev` - Start both backend and frontend
- `build` - Build frontend for production

### 🧪 Testing
- `test-backend` - Test all backend API endpoints
- `test-migration` - Run complete migration test
- `check-integration` - Check if services are running

### 📊 Data Management
- `extract --playlist-id <ID>` - Extract specific playlist
- `logs --service <backend|frontend|both>` - View logs
- `clean-data` - Clean temporary data and logs

### 🛠 Utilities
- `ports` - Show port usage (3000, 8000)
- `kill-servers` - Kill all running servers
- `status` - Show overall project status
- `stats` - Show command usage statistics
- `quick-commands` - Export commands for Cursor

## 🎯 Essential Workflows

### First Time Setup
```bash
# 1. Set up project
python3 cli.py setup

# 2. Start development
python3 cli.py start-dev

# 3. Check status
python3 cli.py status
```

### Daily Development
```bash
# Start development environment
python3 cli.py start-dev

# Or start services individually
python3 cli.py start-backend
python3 cli.py start-frontend

# Check everything is working
python3 cli.py check-integration
```

### Debugging Issues
```bash
# Check what's running on ports
python3 cli.py ports

# View logs
python3 cli.py logs --service backend
python3 cli.py logs --service frontend

# Kill stuck servers
python3 cli.py kill-servers

# Clean install if needed
python3 cli.py clean-install
```

### Testing
```bash
# Test backend APIs
python3 cli.py test-backend

# Run full migration test
python3 cli.py test-migration

# Check integration status
python3 cli.py check-integration
```

## 📊 Command Tracking

The CLI automatically tracks:
- **Command history** - Last 50 commands with timestamps
- **Usage statistics** - How often each command is used
- **Working directory** - Where commands were executed

### View Statistics
```bash
# Show most used and recent commands
python3 cli.py stats

# Export for Cursor integration
python3 cli.py quick-commands
```

## 🎯 Cursor IDE Integration

### Quick Commands File
The CLI generates `QUICK_COMMANDS.md` with:
- 🔥 **Most used commands** (top 5)
- ⏰ **Recently used commands** (last 5)
- 🎯 **Essential commands** (predefined)

### How to Use in Cursor
1. Run `python3 cli.py quick-commands` to update the file
2. Open `QUICK_COMMANDS.md` in Cursor
3. Copy commands directly from the markdown code blocks
4. The file updates automatically with your usage patterns

### Auto-Update Quick Commands
```bash
# Add this to your workflow
python3 cli.py quick-commands && echo "Quick commands updated!"
```

## 🔄 Advanced Usage

### Chaining Commands
```bash
# Clean install and start development
python3 cli.py clean-install && python3 cli.py start-dev

# Test backend and check integration
python3 cli.py test-backend && python3 cli.py check-integration
```

### Background Processes
```bash
# Start backend in background
python3 cli.py start-backend &

# Start frontend in background
python3 cli.py start-frontend &
```

### Custom Scripts
```bash
# Create your own shortcuts
alias anghami-dev="python3 cli.py start-dev"
alias anghami-test="python3 cli.py test-backend && python3 cli.py check-integration"
alias anghami-clean="python3 cli.py kill-servers && python3 cli.py clean-install"
```

## 📁 Data Storage

Command tracking data is stored in:
- `~/.anghami-spotify-cli/command_history.json` - Command history
- `~/.anghami-spotify-cli/usage_stats.json` - Usage statistics

These files persist across sessions and projects.

## 🎨 Command Output

Each command shows:
- 🔧 **Description** - What the command does
- 💻 **Actual command** - The underlying shell command
- ✅/❌ **Result** - Success or failure status

Example:
```
🔧 Test backend health
💻 Command: curl -s http://localhost:8000/health
--------------------------------------------------
{"status":"healthy","timestamp":"2025-01-01T12:00:00","version":"1.0.0"}
✅ Success: Test backend health
```

## 🔧 Troubleshooting

### Common Issues

**CLI not executable:**
```bash
chmod +x cli.py
```

**Commands not found:**
```bash
# Check you're in project root
pwd
# Should show: .../Anghami-Spotify-Migrator

# List available commands
python3 cli.py
```

**Servers won't start:**
```bash
# Kill existing servers
python3 cli.py kill-servers

# Check port availability
python3 cli.py ports

# Clean install dependencies
python3 cli.py clean-install
```

**Quick commands not updating:**
```bash
# Manually regenerate
python3 cli.py quick-commands

# Check file was created
ls -la QUICK_COMMANDS.md
```

## 🎯 Best Practices

1. **Start with setup**: Always run `python3 cli.py setup` for new environments
2. **Use status check**: Run `python3 cli.py status` to see overall health
3. **Track your usage**: Run `python3 cli.py stats` to see your patterns
4. **Update quick commands**: Run `python3 cli.py quick-commands` regularly
5. **Clean when stuck**: Use `python3 cli.py kill-servers` and `clean-install`

## 📈 Productivity Tips

### Cursor Integration
- Pin `QUICK_COMMANDS.md` as a tab for quick access
- Use Cursor's command palette with CLI commands
- Create snippets for frequently used command combinations

### Shell Aliases
Add to your `~/.zshrc` or `~/.bashrc`:
```bash
alias asp="cd /path/to/Anghami-Spotify-Migrator"
alias aspdev="python3 cli.py start-dev"
alias aspstatus="python3 cli.py status"
alias aspquick="python3 cli.py quick-commands"
```

### Workflow Integration
```bash
# Morning startup routine
python3 cli.py status && python3 cli.py start-dev

# End of day cleanup
python3 cli.py kill-servers && python3 cli.py quick-commands
```

This CLI tool is designed to make your development workflow more efficient and provide easy access to the most important commands within Cursor! 