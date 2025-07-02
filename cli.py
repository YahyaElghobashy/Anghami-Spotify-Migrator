#!/usr/bin/env python3
"""
🎵 Anghami → Spotify Migration Tool - Command Line Interface
A comprehensive CLI for managing the migration project with command tracking.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import argparse

# Configuration
CLI_DATA_DIR = Path.home() / ".anghami-spotify-cli"
COMMANDS_HISTORY_FILE = CLI_DATA_DIR / "command_history.json"
USAGE_STATS_FILE = CLI_DATA_DIR / "usage_stats.json"

# Ensure CLI data directory exists
CLI_DATA_DIR.mkdir(exist_ok=True)

class CommandTracker:
    """Track command usage and history for easy access."""
    
    def __init__(self):
        self.history = self._load_history()
        self.stats = self._load_stats()
    
    def _load_history(self) -> List[Dict]:
        """Load command history from file."""
        if COMMANDS_HISTORY_FILE.exists():
            try:
                with open(COMMANDS_HISTORY_FILE, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _load_stats(self) -> Dict[str, int]:
        """Load usage statistics from file."""
        if USAGE_STATS_FILE.exists():
            try:
                with open(USAGE_STATS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_history(self):
        """Save command history to file."""
        with open(COMMANDS_HISTORY_FILE, 'w') as f:
            json.dump(self.history[-50:], f, indent=2)  # Keep last 50 commands
    
    def _save_stats(self):
        """Save usage statistics to file."""
        with open(USAGE_STATS_FILE, 'w') as f:
            json.dump(self.stats, f, indent=2)
    
    def track_command(self, command: str, description: str):
        """Track a command execution."""
        # Update history
        entry = {
            "command": command,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "cwd": os.getcwd()
        }
        self.history.append(entry)
        
        # Update stats
        self.stats[command] = self.stats.get(command, 0) + 1
        
        # Save to files
        self._save_history()
        self._save_stats()
    
    def get_most_used(self, limit: int = 5) -> List[Dict]:
        """Get most used commands."""
        sorted_stats = sorted(self.stats.items(), key=lambda x: x[1], reverse=True)
        return [{"command": cmd, "count": count} for cmd, count in sorted_stats[:limit]]
    
    def get_recent(self, limit: int = 5) -> List[Dict]:
        """Get recently used commands."""
        return self.history[-limit:][::-1]  # Reverse to show most recent first

class AnghamiSpotifyCLI:
    """Main CLI class for Anghami-Spotify migration tool."""
    
    def __init__(self):
        self.tracker = CommandTracker()
        self.project_root = Path(__file__).parent
        
    def run_command(self, cmd: str, description: str, track: bool = True) -> bool:
        """Run a command and optionally track it."""
        if track:
            self.tracker.track_command(cmd, description)
        
        print(f"🔧 {description}")
        print(f"💻 Command: {cmd}")
        print("-" * 50)
        
        try:
            result = subprocess.run(cmd, shell=True, cwd=self.project_root)
            success = result.returncode == 0
            if success:
                print(f"✅ Success: {description}")
            else:
                print(f"❌ Failed: {description}")
            return success
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    # === PROJECT SETUP COMMANDS ===
    def setup_project(self):
        """Set up the complete project environment."""
        commands = [
            ("pip3 install -r requirements.txt", "Install Python dependencies"),
            ("pip3 install -r backend_requirements.txt", "Install backend API dependencies"),
            ("cd ui && npm install", "Install frontend dependencies"),
            ("chmod +x test_integration.sh", "Make integration test script executable"),
        ]
        
        for cmd, desc in commands:
            if not self.run_command(cmd, desc):
                return False
        return True

    def clean_install(self):
        """Clean installation of all dependencies."""
        commands = [
            ("cd ui && rm -rf node_modules package-lock.json", "Clean frontend dependencies"),
            ("cd ui && npm install", "Fresh install frontend dependencies"),
            ("pip3 install --force-reinstall -r requirements.txt", "Reinstall Python dependencies"),
        ]
        
        for cmd, desc in commands:
            self.run_command(cmd, desc)

    # === DEVELOPMENT COMMANDS ===
    def start_backend(self):
        """Start the backend API server."""
        self.run_command("clear && python3 -m backend.main", "Start modular backend API server")

    def start_frontend(self):
        """Start the frontend development server."""
        self.run_command("clear && cd ui && VITE_API_URL=http://localhost:8000 npm run dev", "Start frontend dev server")

    def start_full_dev(self):
        """Start both backend and frontend in development mode."""
        self.run_command("clear && ./test_integration.sh", "Start full development environment")

    def start_both_servers(self):
        """Start both servers in parallel for development."""
        self.run_command("clear && echo '🚀 Starting both servers...' && (python3 -m backend.main &) && (cd ui && VITE_API_URL=http://localhost:8000 npm run dev)", "Start both frontend and backend servers")

    def build_frontend(self):
        """Build the frontend for production."""
        self.run_command("clear && cd ui && npm run build", "Build frontend for production")

    # === TESTING COMMANDS ===
    def test_backend(self):
        """Test backend API endpoints."""
        commands = [
            ("clear", "Clear terminal"),
            ("echo '🧪 Testing Backend API Endpoints...'", "Starting backend tests"),
            ("curl -s http://localhost:8000/health | jq .", "Test backend health"),
            ("curl -s http://localhost:8000/profiles/history | jq .", "Test profiles endpoint"),
            ("curl -s -X POST http://localhost:8000/auth/callback -H 'Content-Type: application/json' -d '{\"code\":\"demo\",\"state\":\"demo\"}'", "Test auth endpoint"),
        ]
        
        for cmd, desc in commands:
            self.run_command(cmd, desc)

    def test_frontend(self):
        """Test frontend application."""
        commands = [
            ("clear", "Clear terminal"),
            ("echo '🎨 Testing Frontend Application...'", "Starting frontend tests"),
            ("cd ui && npm run test -- --run", "Run frontend unit tests"),
            ("curl -s http://localhost:5173 >/dev/null && echo '✅ Frontend reachable' || echo '❌ Frontend not running'", "Check frontend accessibility"),
        ]
        
        for cmd, desc in commands:
            self.run_command(cmd, desc)

    def test_integration(self):
        """Run integration tests."""
        self.run_command("clear && ./test.sh", "Run comprehensive integration tests")

    def test_migration(self):
        """Test the complete migration process."""
        self.run_command("clear && python3 migrate_playlist.py --test", "Run migration test")

    def check_integration(self):
        """Check if both frontend and backend are running."""
        commands = [
            ("clear", "Clear terminal"),
            ("echo '🔍 Checking Service Status...'", "Starting integration check"),
            ("curl -s http://localhost:8000/health | jq .status", "Check backend status"),
            ("curl -s http://localhost:5173 >/dev/null && echo '✅ Frontend OK' || echo '❌ Frontend DOWN'", "Check frontend status"),
            ("lsof -i :8000,5173", "Show port usage for both services"),
        ]
        
        for cmd, desc in commands:
            self.run_command(cmd, desc)

    # === DATA MANAGEMENT COMMANDS ===
    def extract_playlist(self, playlist_id: str):
        """Extract a specific playlist from Anghami."""
        self.run_command(f"python3 src/extractors/anghami_direct_extractor.py {playlist_id}", f"Extract playlist {playlist_id}")

    def view_logs(self, service: str = "both"):
        """View logs for backend, frontend, or both."""
        if service in ["backend", "both"]:
            self.run_command("tail -20 backend.log", "View backend logs")
        if service in ["frontend", "both"]:
            self.run_command("tail -20 frontend.log", "View frontend logs")

    def clean_data(self):
        """Clean temporary data and logs."""
        self.run_command("rm -rf data/temp/* backend.log frontend.log", "Clean temporary data and logs")

    # === UTILITY COMMANDS ===
    def show_ports(self):
        """Show which ports are in use."""
        self.run_command("lsof -i :3000,8000", "Show ports 3000 and 8000 usage")

    def kill_servers(self):
        """Kill any running servers."""
        commands = [
            ("clear", "Clear terminal"),
            ("echo '🛑 Stopping all servers...'", "Starting server shutdown"),
            ("pkill -f 'npm run dev'", "Kill frontend dev server"),
            ("pkill -f 'backend.main'", "Kill modular backend server"),
            ("pkill -f 'uvicorn'", "Kill uvicorn server"),
            ("pkill -f 'backend_api.py'", "Kill legacy backend server (if any)"),
            ("echo '✅ All servers stopped'", "Servers shutdown complete"),
        ]
        
        for cmd, desc in commands:
            self.run_command(cmd, desc)

    def show_project_status(self):
        """Show overall project status."""
        print("🎵 Anghami → Spotify Migration Tool Status")
        print("=" * 50)
        
        # Check dependencies
        print("\n📦 Dependencies:")
        subprocess.run("python3 --version", shell=True)
        subprocess.run("node --version", shell=True)
        subprocess.run("npm --version", shell=True)
        
        # Check servers
        print("\n🌐 Services:")
        self.check_integration()
        
        # Show recent activity
        print("\n📊 Recent Commands:")
        recent = self.tracker.get_recent(5)
        for i, cmd in enumerate(recent, 1):
            print(f"{i}. {cmd['command']} - {cmd['description']}")

    # === COMMAND TRACKING UTILITIES ===
    def show_command_stats(self):
        """Show command usage statistics."""
        print("🎯 Command Usage Statistics")
        print("=" * 50)
        
        print("\n🔥 Most Used Commands:")
        most_used = self.tracker.get_most_used(5)
        for i, cmd in enumerate(most_used, 1):
            print(f"{i}. {cmd['command']} (used {cmd['count']} times)")
        
        print("\n⏰ Recently Used Commands:")
        recent = self.tracker.get_recent(5)
        for i, cmd in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(cmd['timestamp']).strftime("%m/%d %H:%M")
            print(f"{i}. {cmd['command']} ({timestamp})")


    def upcom(self):
        """Update and display quick commands in terminal format."""
        display_script = self.project_root / ".quick-commands" / "display.py"
        self.run_command(f'python3 "{display_script}"', "Update and display quick commands", track=False)

    def excom(self):
        """Display all commands categorized in terminal format."""
        display_script = self.project_root / ".quick-commands" / "display.py"
        self.run_command(f'python3 "{display_script}" all', "Display all commands categorized", track=False)

    def show_quick_commands(self):
        """Show most used and recent commands in terminal format."""
        print("🚀 Quick Commands - Anghami Spotify Migration")
        print("=" * 50)
        
        print("\n🔥 Most Used Commands:")
        most_used = self.tracker.get_most_used(5)
        for i, cmd in enumerate(most_used, 1):
            print(f"  {i}. {cmd['command']} (used {cmd['count']} times)")
        
        print("\n⏰ Recently Used Commands:")
        recent = self.tracker.get_recent(5)
        for i, cmd in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(cmd['timestamp']).strftime("%m/%d %H:%M")
            print(f"  {i}. {cmd['command']} ({timestamp})")

    def export_quick_commands(self):
        """Export quick commands for Cursor integration."""
        quick_commands_file = self.project_root / "QUICK_COMMANDS.md"
        
        most_used = self.tracker.get_most_used(5)
        recent = self.tracker.get_recent(5)
        
        content = f"""# 🚀 Quick Commands - Anghami Spotify Migration

*Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

## 🔥 Most Used Commands

"""
        
        for i, cmd in enumerate(most_used, 1):
            content += f"### {i}. Most Used Command\n```bash\n{cmd['command']}\n```\n*Used {cmd['count']} times*\n\n"
        
        content += "## ⏰ Recently Used Commands\n\n"
        
        for i, cmd in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(cmd['timestamp']).strftime("%m/%d %H:%M")
            content += f"### {i}. Recent Command ({timestamp})\n```bash\n{cmd['command']}\n```\n*{cmd['description']}*\n\n"
        
        content += """## 🎯 Essential Commands

### Development
```bash
# Start full development environment
./test_integration.sh

# Start backend only
python3 backend_api.py

# Start frontend only
cd ui && VITE_API_URL=http://localhost:8000 npm run dev
```

### Testing
```bash
# Test backend health
curl -s http://localhost:8000/health

# Check integration status
python3 cli.py check-integration

# View logs
tail -f backend.log
tail -f frontend.log
```

### Maintenance
```bash
# Kill all servers
python3 cli.py kill-servers

# Clean install
python3 cli.py clean-install

# Show project status
python3 cli.py status
```
"""
        
        with open(quick_commands_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Quick commands exported to: {quick_commands_file}")
        print("📋 You can now access this file in Cursor for easy copy-paste!")

    def restart(self):
        """Restart both frontend and backend servers, ensuring all relevant ports are free."""
        commands = [
            ("clear", "Clear terminal"),
            ("echo '🔄 Restarting all servers (backend:8000, frontend:3000/5173)...'", "Announce restart"),
            # Kill all relevant ports (3000, 5173, 8000)
            ("lsof -ti :3000,5173,8000 | xargs kill -9 2>/dev/null || true", "Kill processes on ports 3000, 5173, 8000 (if any)"),
            # Also kill by process name for robustness
            ("pkill -f 'npm run dev' || true", "Kill frontend dev server by name"),
            ("pkill -f 'backend.main' || true", "Kill modular backend server by name"),
            ("pkill -f 'uvicorn' || true", "Kill uvicorn server by name"),
            ("pkill -f 'backend_api.py' || true", "Kill legacy backend server by name"),
            ("sleep 2", "Wait for ports to be released"),
            ("echo '✅ All servers stopped. Starting backend on 8000 and frontend on 3000...'", "Announce startup"),
            # Start backend
            ("(python3 -m backend.main &)", "Start backend server on 8000"),
            # Start frontend (on 3000)
            ("(cd ui && VITE_API_URL=http://localhost:8000 npm run dev -- --port 3000 &)", "Start frontend dev server on 3000"),
            ("sleep 3", "Wait for servers to start"),
            ("echo '🚀 Backend: http://localhost:8000 | Frontend: http://localhost:3000'", "Show URLs"),
        ]
        for cmd, desc in commands:
            self.run_command(cmd, desc, track=False)

def main():
    """Main CLI entry point."""
    cli = AnghamiSpotifyCLI()
    
    parser = argparse.ArgumentParser(description="Anghami → Spotify Migration Tool CLI")
    parser.add_argument('command', nargs='?', help='Command to run')
    parser.add_argument('--playlist-id', help='Playlist ID for extraction')
    parser.add_argument('--service', choices=['backend', 'frontend', 'both'], default='both', help='Service for logs')
    
    args = parser.parse_args()
    
    if not args.command:
        print("🎵 Anghami → Spotify Migration Tool CLI")
        print("=" * 50)
        print("Available commands:")
        print("  setup           - Set up project environment")
        print("  clean-install   - Clean install all dependencies")
        print("")
        print("🔧 Development:")
        print("  start-backend   - Start modular backend API server")
        print("  start-frontend  - Start frontend dev server")
        print("  start-both      - Start both servers in parallel")
        print("  start-dev       - Start full development environment")
        print("  restart         - Restart both servers (force kill + start)")
        print("  build           - Build frontend for production")
        print("")
        print("🧪 Testing:")
        print("  test-backend    - Test backend API endpoints")
        print("  test-frontend   - Test frontend application")
        print("  test-integration - Run comprehensive integration tests")
        print("  test-migration  - Test migration process")
        print("  check-integration - Check if services are running")
        print("")
        print("📊 Data Management:")
        print("  extract         - Extract playlist (requires --playlist-id)")
        print("  logs            - View logs (use --service)")
        print("  clean-data      - Clean temporary data")
        print("")
        print("🛠️ Utilities:")
        print("  ports           - Show port usage")
        print("  kill-servers    - Kill running servers")
        print("  status          - Show project status")
        print("  stats           - Show command usage statistics")
        print("")
        print("📋 Quick Access:")
        print("  upcom           - Show quick commands")
        print("  excom           - Display all commands categorized")
        print("  quick-show      - Show most used and recent commands")
        print("  quick-commands  - Export quick commands for Cursor")
        print("")
        print("Usage: python3 cli.py <command> [options]")
        return
    
    # Command mapping
    commands = {
        'setup': cli.setup_project,
        'clean-install': cli.clean_install,
        'start-backend': cli.start_backend,
        'start-frontend': cli.start_frontend,
        'start-dev': cli.start_full_dev,
        'start-both': cli.start_both_servers,
        'restart': cli.restart,
        'build': cli.build_frontend,
        'test-backend': cli.test_backend,
        'test-frontend': cli.test_frontend,
        'test-integration': cli.test_integration,
        'test-migration': cli.test_migration,
        'check-integration': cli.check_integration,
        'logs': lambda: cli.view_logs(args.service),
        'clean-data': cli.clean_data,
        'ports': cli.show_ports,
        'kill-servers': cli.kill_servers,
        'status': cli.show_project_status,
        'stats': cli.show_command_stats,
        'upcom': cli.upcom,
        'excom': cli.excom,
        'quick-show': cli.show_quick_commands,
        'quick-commands': cli.export_quick_commands,
    }
    
    if args.command == 'extract':
        if not args.playlist_id:
            print("❌ Error: --playlist-id required for extract command")
            return
        cli.extract_playlist(args.playlist_id)
    elif args.command in commands:
        commands[args.command]()
    else:
        print(f"❌ Unknown command: {args.command}")
        print("Run 'python3 cli.py' to see available commands")

if __name__ == "__main__":
    main() 