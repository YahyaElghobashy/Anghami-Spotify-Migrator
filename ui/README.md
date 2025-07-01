# 🎵 Anghami → Spotify Migration Tool - UI System

A modern, accessible, and beautiful user interface for the Anghami to Spotify playlist migration tool. Built with React, TypeScript, Tailwind CSS, and following best practices for UX/UI design.

## ✨ Features

### 🎨 **Modern Design System**
- **Brand-Aware**: Spotify green + Anghami purple color palette
- **Responsive**: Mobile-first design that works on all devices
- **Dark Mode**: Automatic theme switching with system preference detection
- **Accessibility**: WCAG AA compliant with keyboard navigation and screen reader support

### 🚀 **Complete User Flow**
1. **Authentication Screen**: Secure OAuth2 flow with clear privacy messaging
2. **Playlist Selection**: Interactive playlist browser with search and filtering
3. **Arabic Track Review**: Special interface for reviewing Arabic track matches
4. **Real-time Migration**: Live progress tracking with detailed feedback
5. **Results Summary**: Complete migration report with statistics

### ⚡ **Performance & Animation**
- **Smooth Animations**: Framer Motion powered micro-interactions
- **Optimized**: Tree-shaken bundle with lazy loading
- **Fast**: Vite-powered development with hot module replacement

## 🏗️ Architecture

```
ui/
├── src/
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── Button.tsx    # All button variants
│   │   │   ├── Card.tsx      # Card components with hover effects
│   │   │   ├── Input.tsx     # Form inputs with validation
│   │   │   └── Progress.tsx  # Progress bars and indicators
│   │   └── layout/
│   │       └── AppLayout.tsx # Main application layout
│   ├── screens/
│   │   └── AuthScreen.tsx    # Authentication flow
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # React entry point
│   └── index.css            # Global styles
├── package.json             # Dependencies and scripts
├── tailwind.config.js       # Design system configuration
└── vite.config.ts          # Build configuration
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Modern browser with ES2020 support

### Installation

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
# Create production build
npm run build

# Preview production build
npm run preview
```

## 🎯 Component Library

### Button Component

```tsx
import { Button } from './components/ui/Button';

// Primary action button
<Button variant="primary" size="lg" loading={isLoading}>
  Start Migration
</Button>

// Secondary button with icon
<Button variant="secondary" leftIcon={<Search />}>
  Search Playlists
</Button>
```

**Available Variants:**
- `primary` - Spotify green, main actions
- `secondary` - Neutral gray, secondary actions  
- `ghost` - Transparent, subtle actions
- `destructive` - Red, dangerous actions

### Card Component

```tsx
import { Card, CardHeader, CardContent } from './components/ui/Card';

<Card clickable hover>
  <CardHeader>
    <h3>Playlist Title</h3>
  </CardHeader>
  <CardContent>
    <p>Playlist details...</p>
  </CardContent>
</Card>
```

### Progress Components

```tsx
import { ProgressBar, CircularProgress, StepProgress } from './components/ui/Progress';

// Linear progress bar
<ProgressBar value={75} showLabel label="Migration Progress" />

// Circular progress indicator
<CircularProgress value={60} showLabel />

// Step-by-step progress
<StepProgress steps={[
  { title: 'Authenticate', status: 'completed' },
  { title: 'Select', status: 'current' },
  { title: 'Migrate', status: 'pending' }
]} />
```

## 🔗 Backend Integration

### API Connection

The UI is designed to work with the Python migration backend. To connect:

1. **Update API endpoints** in a configuration file:

```typescript
// src/config/api.ts
export const API_CONFIG = {
  BASE_URL: process.env.VITE_API_URL || 'http://localhost:8000',
  ENDPOINTS: {
    AUTH: '/auth/spotify',
    PLAYLISTS: '/playlists',
    MIGRATE: '/migrate',
    STATUS: '/status'
  }
};
```

2. **Implement API calls** using fetch or axios:

```typescript
// src/api/client.ts
export async function authenticateSpotify() {
  const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.AUTH}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  return response.json();
}

export async function getPlaylists() {
  const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.PLAYLISTS}`);
  return response.json();
}

export async function startMigration(playlistIds: string[]) {
  const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.MIGRATE}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ playlist_ids: playlistIds })
  });
  return response.json();
}
```

3. **Replace mock data** in `App.tsx` with real API calls.

### WebSocket Integration

For real-time migration progress:

```typescript
// src/hooks/useWebSocket.ts
export function useWebSocket(url: string) {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<any[]>([]);

  useEffect(() => {
    const ws = new WebSocket(url);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setMessages(prev => [...prev, data]);
    };
    setSocket(ws);
    return () => ws.close();
  }, [url]);

  return { socket, messages };
}
```

## 🎨 Design System

### Color Palette

```css
/* Spotify Brand */
--spotify-500: #10b981;  /* Primary actions */
--spotify-600: #059669;  /* Hover states */

/* Anghami Brand */
--anghami-600: #c026d3;  /* Accents */
--anghami-700: #a21caf;  /* Links */

/* Neutral System */
--slate-50: #f8fafc;     /* Light backgrounds */
--slate-900: #0f172a;    /* Dark backgrounds */
```

### Typography Scale

```css
/* Display Headlines */
.text-display     /* 36px / 40px - Main headers */
.text-display-sm  /* 30px / 36px - Section headers */

/* Body Text */
text-lg          /* 18px - Descriptions */
text-base        /* 16px - Body text */
text-sm          /* 14px - Labels */
text-xs          /* 12px - Captions */
```

### Responsive Breakpoints

```css
sm:   /* 640px+ - Mobile landscape */
md:   /* 768px+ - Tablet portrait */
lg:   /* 1024px+ - Desktop */
xl:   /* 1280px+ - Large desktop */
```

## 🌐 Accessibility Features

- **Keyboard Navigation**: Full keyboard support with logical tab order
- **Screen Readers**: Proper ARIA labels and semantic HTML
- **Color Contrast**: WCAG AA compliant (4.5:1 minimum)
- **Reduced Motion**: Respects `prefers-reduced-motion` setting
- **Focus Management**: Visible focus indicators and focus trapping in modals

## 🧪 Testing

```bash
# Run type checking
npm run type-check

# Run linting
npm run lint

# Run tests (when implemented)
npm run test
```

## 📱 Browser Support

- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **Mobile**: iOS Safari 14+, Chrome Mobile 90+
- **Features**: ES2020, CSS Grid, Flexbox, CSS Custom Properties

## 🔧 Environment Variables

Create a `.env` file in the UI directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# Spotify Configuration (if handling OAuth in frontend)
VITE_SPOTIFY_CLIENT_ID=your_spotify_client_id
VITE_SPOTIFY_REDIRECT_URI=http://localhost:3000/callback

# Feature Flags
VITE_ENABLE_DARK_MODE=true
VITE_ENABLE_ANALYTICS=false
```

## 🚀 Deployment

### Production Build

```bash
# Build optimized bundle
npm run build

# Output will be in dist/ directory
# Serve with any static file server
```

### Docker Deployment

```dockerfile
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 🤝 Contributing

1. **Follow Design Guidelines**: Stick to the established design system
2. **Accessibility First**: Ensure all components are accessible
3. **Mobile Responsive**: Test on mobile devices
4. **Type Safety**: Use TypeScript for all new code
5. **Performance**: Keep bundle size optimized

## 📚 Additional Resources

- [Design Guidelines](.cursor/design-guidelines.mdc) - Complete design system specification
- [Tailwind CSS Docs](https://tailwindcss.com/docs) - Utility-first CSS framework
- [Framer Motion](https://www.framer.com/motion/) - Animation library
- [Headless UI](https://headlessui.com/) - Accessible component primitives
- [React Hook Form](https://react-hook-form.com/) - Form handling
- [Lucide Icons](https://lucide.dev/) - Icon library

---

**Built with ❤️ for seamless music migration** 