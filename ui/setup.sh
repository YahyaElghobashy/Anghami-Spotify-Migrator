#!/bin/bash

# 🎵 Anghami → Spotify Migration Tool - UI Setup Script
# This script sets up the React UI application

set -e

echo "🎵 Setting up Anghami → Spotify Migration Tool UI..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    echo "   Visit: https://nodejs.org/en/download/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version 18+ is required. Current version: $(node -v)"
    echo "   Please upgrade Node.js: https://nodejs.org/en/download/"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ package.json not found. Please run this script from the ui/ directory"
    exit 1
fi

echo "📦 Installing dependencies..."
echo ""

# Install dependencies
if command -v npm &> /dev/null; then
    npm install
    echo ""
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ npm not found. Please install Node.js with npm."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cat > .env << EOF
# API Configuration - Update these URLs to match your backend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Spotify Configuration (if handling OAuth in frontend)
VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id
VITE_SPOTIFY_REDIRECT_URI=http://localhost:3000/callback

# Feature Flags
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_ANALYTICS=false
EOF
    echo "✅ Environment file created (.env)"
    echo "   📝 Please update the API URLs in .env to match your backend"
else
    echo "✅ Environment file already exists (.env)"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🚀 Quick Start Commands:"
echo "   npm run dev      # Start development server (localhost:3000)"
echo "   npm run build    # Build for production" 
echo "   npm run preview  # Preview production build"
echo "   npm run lint     # Check code quality"
echo ""
echo "📋 Next Steps:"
echo "   1. Update API URLs in .env file to match your backend"
echo "   2. Run 'npm run dev' to start the development server"
echo "   3. Open http://localhost:3000 in your browser"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Complete setup and usage guide"
echo "   - src/components/ - Reusable UI components"
echo "   - .cursor/design-guidelines.mdc - Design system specification"
echo ""
echo "🐛 Troubleshooting:"
echo "   - Make sure your backend is running on the configured port"
echo "   - Check browser console for any JavaScript errors"
echo "   - Verify all environment variables are set correctly"
echo ""
echo "Happy coding! 🎶" 