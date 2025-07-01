# Anghami → Spotify Migration Tool

A comprehensive tool for migrating your music playlists from Anghami to Spotify with a modern React frontend, FastAPI backend, and automated testing suite.

## ✨ Features

- **Multi-User System**: Secure user management with encrypted credentials
- **Real-Time Profile Validation**: Live extraction of Anghami profile data including avatars
- **Profile Picture Support**: Displays actual user avatars throughout the interface
- **Timeline Progress Tracking**: Beautiful animated timeline showing migration progress
- **Responsive Design**: Works seamlessly across desktop, tablet, and mobile
- **Comprehensive Testing**: Full end-to-end test coverage with Playwright
- **Modern UI**: Clean, professional interface following design system guidelines

## 🏗️ Repository Structure

```
Anghami-Spotify-Migrator/
├── 📁 tests/                    # Testing infrastructure
│   ├── 📁 e2e/                 # End-to-end test suites
│   │   └── e2e_full_journey.spec.js
│   ├── 📁 config/              # Test configurations
│   │   └── playwright.config.js
│   ├── 📁 scripts/             # Test runner scripts
│   │   └── run_tests.sh
│   ├── global-setup.js         # Test environment setup
│   └── global-teardown.js      # Test cleanup
├── 📁 src/                     # Backend source code
│   ├── 📁 auth/                # Authentication modules
│   ├── 📁 extractors/          # Data extraction engines
│   ├── 📁 models/              # Data models
│   └── 📁 utils/               # Utility functions
├── 📁 ui/                      # React frontend application
│   ├── 📁 src/
│   │   ├── 📁 components/      # Reusable UI components
│   │   │   ├── 📁 layout/      # Layout components
│   │   │   └── 📁 ui/          # Base UI components
│   │   ├── 📁 screens/         # Application screens
│   │   └── 📁 api/             # API client
│   └── package.json
├── 📁 docs/                    # Documentation
├── 📁 config/                  # Application configuration
├── 📁 data/                    # Runtime data and logs
├── 📁 scripts/                 # Build and utility scripts
├── backend_api.py              # FastAPI backend server
├── test.sh                     # Convenient test runner
└── README.md
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** (v16 or higher)
- **Python** (v3.8 or higher)
- **npm** or **yarn**

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Anghami-Spotify-Migrator
   ```

2. **Install backend dependencies**
   ```bash
   pip install -r backend_requirements.txt
   ```

3. **Install frontend dependencies**
   ```bash
   cd ui
   npm install
   cd ..
   ```

4. **Setup testing environment** (optional)
   ```bash
   ./test.sh -s
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   python backend_api.py
   ```

2. **Start the frontend development server**
   ```bash
   cd ui
   npm run dev
   ```

3. **Open your browser**
   ```
   http://localhost:5173
   ```

## 🧪 Testing

### Comprehensive Test Suite

Our testing infrastructure includes 11 comprehensive test scenarios covering the complete user journey:

1. **Initial App Load** - Setup screen validation
2. **User Registration** - Form validation and account creation  
3. **Spotify Authentication** - Setup guide and credentials
4. **Profile Input** - Real-time validation with actual Anghami profiles
5. **Navigation System** - Back buttons and step navigation
6. **Responsive Design** - Mobile, tablet, desktop layouts
7. **Component Interactions** - Buttons, cards, form inputs
8. **Error Handling** - Network errors and edge cases
9. **Performance Testing** - Load times and memory usage
10. **Accessibility** - Keyboard navigation and ARIA compliance
11. **Test Summary** - Comprehensive reporting

### Running Tests

```bash
# Run all tests
./test.sh

# Run tests in specific browser
./test.sh -b firefox

# Run mobile tests
./test.sh -p mobile-chrome

# Run tests in debug mode (with UI)
./test.sh -d

# Run specific test
./test.sh -t "profile input"

# Setup environment only
./test.sh -s

# Open test report after completion
./test.sh -r
```

### Test Configuration

The test suite supports multiple browsers and viewports:
- **Desktop**: Chrome, Firefox, Safari
- **Mobile**: Chrome Mobile, Safari Mobile
- **Tablet**: iPad Pro

Results are automatically saved to:
- **HTML Report**: `data/test-results/html-report/index.html`
- **Screenshots**: `data/screenshots/`
- **Logs**: `data/logs/`

## 🎨 UI Components

### Design System

Our component library follows a systematic design approach:

- **Colors**: Spotify Green (`emerald-600`) + Anghami Purple (`fuchsia-600`)
- **Typography**: System font stack with proper hierarchy
- **Spacing**: Consistent spacing using Tailwind utilities
- **Animations**: Smooth transitions with Framer Motion

### Key Components

- **Timeline**: Animated progress tracking with step details
- **ScreenTransition**: Smooth fade transitions between screens
- **Button**: Multiple variants (primary, secondary, ghost, destructive)
- **Card**: Clean content containers with hover effects
- **Avatar Display**: Automatic image loading with fallbacks

### Component Documentation

Comprehensive component documentation is available at:
📖 [UI Component Library Guide](ui/src/components/README.md)

## 🔧 Backend Features

### Profile Extraction Engine

- **Real-Time Validation**: Live Anghami profile verification
- **Avatar Extraction**: Automatic profile picture retrieval
- **Music Data**: Most played songs and listening history
- **Follower Count**: Social metrics extraction

### Multi-User System

- **Secure Authentication**: Fernet encryption for credentials
- **Session Management**: Secure token-based sessions
- **Profile History**: Recent profile usage tracking
- **User Isolation**: Individual encryption keys per user

### Database Schema

```sql
-- User credentials with encryption
users (id, username, encrypted_password, salt, created_at)

-- Profile history tracking
profile_history (id, profile_url, display_name, avatar_url, follower_count, usage_count, last_used)

-- User sessions
user_sessions (token, username, created_at, expires_at)
```

## 🌟 New Features in v2.0.0

### ✅ Simplified Navigation
- Clean top bar with only essential elements
- Timeline-based progress tracking on the right
- Smooth screen transitions with fade animations

### ✅ Profile Picture Support
- Real avatar extraction from Anghami profiles
- Displays user photos throughout the interface
- Intelligent fallbacks for missing images

### ✅ Enhanced Testing
- Complete end-to-end test coverage
- Multi-browser and responsive testing
- Performance and accessibility validation

### ✅ Repository Organization
- Proper folder structure for maintainability
- Separated concerns (tests, docs, src)
- Convenient script wrappers

## 📸 Screenshots

### Profile Validation with Avatar Support
The tool now extracts and displays actual user profile pictures from Anghami accounts.

### Timeline Progress Tracking  
Beautiful animated timeline shows your migration progress with detailed step information.

### Responsive Design
Works perfectly across all device sizes with adaptive layouts.

## 🐛 Troubleshooting

### Common Issues

1. **Profile pictures not loading**
   - Check network connectivity
   - Verify Anghami profile is public
   - Avatar fallback icons will display automatically

2. **Tests failing**
   - Ensure both frontend and backend servers are running
   - Check port availability (3000, 8000)
   - Run `./test.sh -s` to setup environment

3. **Build issues**
   - Clear node_modules and reinstall: `cd ui && rm -rf node_modules && npm install`
   - Check Python dependencies: `pip install -r backend_requirements.txt`

### Getting Help

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Check the `docs/` folder for detailed guides
- **Component Docs**: See `ui/src/components/README.md`

## 🎯 Roadmap

- **Phase C**: Real playlist integration and migration
- **Phase D**: Enhanced analytics and reporting
- **Phase E**: Bulk migration and scheduling

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ using React, TypeScript, FastAPI, and Playwright** 