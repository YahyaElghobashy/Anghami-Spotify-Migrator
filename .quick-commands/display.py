#!/usr/bin/env python3
"""
Quick Commands Display System
Shows the most used and categorized commands for the Anghami-Spotify Migration Tool.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Configuration
CLI_DATA_DIR = Path.home() / ".anghami-spotify-cli"
COMMANDS_HISTORY_FILE = CLI_DATA_DIR / "command_history.json"
USAGE_STATS_FILE = CLI_DATA_DIR / "usage_stats.json"

def load_stats():
    """Load usage statistics from file."""
    if USAGE_STATS_FILE.exists():
        try:
            with open(USAGE_STATS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def load_history():
    """Load command history from file."""
    if COMMANDS_HISTORY_FILE.exists():
        try:
            with open(COMMANDS_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def get_most_used(stats, limit=5):
    """Get most used commands."""
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    return [{"command": cmd, "count": count} for cmd, count in sorted_stats[:limit]]

def get_recent(history, limit=5):
    """Get recently used commands."""
    return history[-limit:][::-1]  # Reverse to show most recent first

def display_quick_commands():
    """Display the most used and recent commands."""
    print("\n🚀 Anghami → Spotify Migration Tool - Quick Commands")
    print("=" * 60)
    
    stats = load_stats()
    history = load_history()
    
    # Most Used Commands
    print("\n🔥 Most Used Commands:")
    most_used = get_most_used(stats, 5)
    if most_used:
        for i, cmd in enumerate(most_used, 1):
            print(f"  {i}. {cmd['command']} (used {cmd['count']} times)")
    else:
        print("  No commands used yet")
    
    # Recent Commands
    print("\n⏰ Recently Used Commands:")
    recent = get_recent(history, 5)
    if recent:
        for i, cmd in enumerate(recent, 1):
            timestamp = datetime.fromisoformat(cmd['timestamp']).strftime("%m/%d %H:%M")
            print(f"  {i}. {cmd['command']} ({timestamp})")
    else:
        print("  No recent commands")
    
    print("\n💡 Run 'python3 cli.py <command>' to execute any command")
    print("📋 Run 'python3 .quick-commands/display.py all' for all available commands")

def display_all_commands():
    """Display all available commands categorized."""
    print("\n🎵 Anghami → Spotify Migration Tool - All Commands")
    print("=" * 60)
    
    commands = {
        "🚀 Project Setup": [
            ("setup", "Set up project environment"),
            ("clean-install", "Clean install all dependencies"),
        ],
        "🔧 Development": [
            ("start-backend", "Start modular backend API server"),
            ("start-frontend", "Start frontend dev server"),
            ("start-both", "Start both servers in parallel"),
            ("start-dev", "Start full development environment"),
            ("build", "Build frontend for production"),
        ],
        "🧪 Testing": [
            ("test-backend", "Test backend API endpoints"),
            ("test-frontend", "Test frontend application"),
            ("test-integration", "Run comprehensive integration tests"),
            ("test-migration", "Test migration process"),
            ("check-integration", "Check if services are running"),
        ],
        "📊 Data Management": [
            ("extract <playlist-id>", "Extract playlist from Anghami"),
            ("logs [service]", "View logs (backend/frontend/both)"),
            ("clean-data", "Clean temporary data"),
        ],
        "🛠️ Utilities": [
            ("ports", "Show port usage"),
            ("kill-servers", "Kill running servers"),
            ("status", "Show project status"),
            ("stats", "Show command usage statistics"),
        ],
        "📋 Quick Access": [
            ("upcom", "Show quick commands"),
            ("excom", "Display all commands categorized"),
            ("quick-show", "Show most used commands"),
            ("quick-commands", "Export quick commands for Cursor"),
        ]
    }
    
    for category, cmds in commands.items():
        print(f"\n{category}")
        print("-" * 40)
        for cmd, desc in cmds:
            print(f"  {cmd:<20} - {desc}")
    
    print(f"\n📈 Usage Statistics:")
    stats = load_stats()
    if stats:
        total_commands = sum(stats.values())
        unique_commands = len(stats)
        print(f"  Total commands executed: {total_commands}")
        print(f"  Unique commands used: {unique_commands}")
    else:
        print("  No usage statistics available yet")
    
    print(f"\n⚡ Quick Tips:")
    print(f"  • Run 'python3 cli.py start-both' to start both servers quickly")
    print(f"  • Use 'python3 cli.py kill-servers' to stop all running services")
    print(f"  • Run 'python3 cli.py check-integration' to verify everything is working")
    print(f"  • Use './test.sh' for comprehensive testing")
    print(f"  • Check backend and frontend logs for debugging")

def main():
    """Main entry point."""
    show_all = len(sys.argv) > 1 and sys.argv[1] == "all"
    
    if show_all:
        display_all_commands()
    else:
        display_quick_commands()

if __name__ == "__main__":
    main() 