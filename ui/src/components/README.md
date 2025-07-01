# UI Component Library

This document describes the reusable UI components built for the Anghami-Spotify Migration Tool, following the established design guidelines for consistent, accessible, and maintainable user interfaces.

## Design System

### Color Palette

Our design system follows a carefully curated color palette that bridges both music services:

- **Spotify Green**: `emerald-500/emerald-600` - Primary actions and success states
- **Anghami Purple**: `fuchsia-600/fuchsia-700` - Accents, selection states, and branding
- **Neutral Canvas**: `slate-50-slate-900` - Backgrounds and text with full dark mode support
- **Status Colors**: 
  - Info: `sky-500` - Progress bars and informational content
  - Warning: `amber-500` - Rate limits and cautionary messages
  - Danger: `rose-600` - Destructive actions and error states

### Typography Scale

Following a systematic hierarchy for optimal readability:

- **Display/H1**: `font-sans text-3xl md:text-4xl font-extrabold tracking-tight`
- **Section Headings**: `text-xl md:text-2xl font-semibold`
- **Body Text**: `text-base leading-relaxed`
- **Code/CLI**: `font-mono text-sm`

### Spacing & Layout

- **Container**: `container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8`
- **Grid System**: Mobile-first responsive with `gap-*` utilities
- **Component Spacing**: Consistent `space-y-*` and `space-x-*` patterns

## Component Library

### Button Component

A versatile button component with multiple variants and consistent interaction patterns.

#### Usage

```tsx
import { Button } from './components/ui/Button';

// Primary action button (Spotify green)
<Button variant="primary" size="lg" onClick={handleSubmit}>
  Continue Migration
</Button>

// Secondary neutral button
<Button variant="secondary" size="md" onClick={handleCancel}>
  Cancel
</Button>

// Ghost button for minimal actions
<Button variant="ghost" size="sm" onClick={handleHelp}>
  Help
</Button>

// Destructive action button
<Button variant="destructive" size="md" onClick={handleDelete}>
  Delete Playlist
</Button>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `variant` | `'primary' \| 'secondary' \| 'ghost' \| 'destructive'` | `'primary'` | Visual style variant |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Button size |
| `loading` | `boolean` | `false` | Shows loading spinner and disables interaction |
| `disabled` | `boolean` | `false` | Disables the button |
| `className` | `string` | - | Additional CSS classes |

#### Design Guidelines

- **Primary**: Use for main actions like "Continue", "Start Migration"
- **Secondary**: Use for alternative actions like "Cancel", "Back"
- **Ghost**: Use for toolbar actions and subtle interactions
- **Destructive**: Use for dangerous actions like "Delete", "Reset"

#### Accessibility

- Automatic `disabled` state management
- Focus ring with `focus:ring-2 focus:ring-emerald-500`
- Loading state with spinner and disabled interaction
- Keyboard navigation support

---

### Card Component

Clean, minimal cards for content organization with subtle shadows and hover effects.

#### Usage

```tsx
import { Card, CardHeader, CardContent } from './components/ui/Card';

<Card>
  <CardHeader>
    <h2 className="text-xl md:text-2xl font-semibold">Profile Information</h2>
    <p className="text-base leading-relaxed text-slate-600 dark:text-slate-400">
      Your Anghami profile details
    </p>
  </CardHeader>
  <CardContent>
    <div className="space-y-4">
      {/* Card content */}
    </div>
  </CardContent>
</Card>

// Clickable card variant
<Card clickable hover onClick={handleCardClick}>
  <CardContent>
    <div>Interactive card content</div>
  </CardContent>
</Card>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `clickable` | `boolean` | `false` | Makes card interactive with hover and click effects |
| `hover` | `boolean` | `true` | Enables hover shadow effects |
| `className` | `string` | - | Additional CSS classes |

#### Design Guidelines

- **Base Style**: `rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm`
- **Hover Effect**: `hover:shadow-md transition-shadow duration-300`
- **Clickable Enhancement**: Subtle scale and translate effects for interaction feedback

#### Layout Structure

- **CardHeader**: `p-6 pb-4` - Contains titles and descriptions
- **CardContent**: `px-6 pb-6` - Main content area with consistent padding

---

### AppLayout Component

The main application shell providing navigation, progress tracking, and responsive layout management.

#### Usage

```tsx
import { AppLayout } from './components/layout/AppLayout';

<AppLayout
  currentStep={2}
  totalSteps={6}
  userSession={userSession}
  canNavigateBack={true}
  onBackClick={handleBackNavigation}
  onStepClick={handleStepNavigation}
  onLogoClick={handleLogoClick}
  onProfileClick={handleProfileClick}
  sidebar={<ProfileSidebar />}
>
  <ProfileInputScreen />
</AppLayout>
```

#### Features

1. **Clean Header Design**
   - Proper 16px height following design guidelines
   - Clean logo with Anghami (purple) → Spotify (green) branding
   - Desktop step navigation with progress indicators
   - Mobile-responsive progress bar

2. **Navigation System**
   - Back button with consistent styling
   - Step-based navigation for completed/current steps
   - User profile dropdown integration

3. **Responsive Layout**
   - Mobile-first design with breakpoint-specific adaptations
   - Container-based layout: `max-w-7xl` with responsive padding
   - Grid system supporting sidebar layout

#### Props

| Prop | Type | Description |
|------|------|-------------|
| `currentStep` | `number` | Current step in the migration process (1-6) |
| `totalSteps` | `number` | Total number of steps in the process |
| `userSession` | `object` | User session data for profile display |
| `canNavigateBack` | `boolean` | Enables back navigation button |
| `onBackClick` | `function` | Handler for back navigation |
| `onStepClick` | `function` | Handler for step navigation clicks |
| `sidebar` | `ReactNode` | Optional sidebar content |

#### Step Configuration

```tsx
const steps = [
  { id: 1, name: 'Setup', description: 'Account setup', key: 'setup' },
  { id: 2, name: 'Profile', description: 'Anghami profile', key: 'profile' },
  { id: 3, name: 'Authenticate', description: 'Connect Spotify', key: 'auth' },
  { id: 4, name: 'Select', description: 'Choose playlists', key: 'select' },
  { id: 5, name: 'Migrate', description: 'Transfer to Spotify', key: 'migrate' },
  { id: 6, name: 'Complete', description: 'Migration summary', key: 'complete' },
];
```

---

### Form Components

#### Input Component

Clean, accessible form inputs with validation states and consistent styling.

```tsx
import { Input } from './components/ui/Input';

<Input
  type="url"
  placeholder="https://play.anghami.com/profile/username"
  value={profileUrl}
  onChange={handleUrlChange}
  className={`transition-all duration-300 ease-in-out ${
    validationState === 'valid' ? 'border-emerald-500 focus:ring-emerald-500' :
    validationState === 'invalid' ? 'border-rose-600 focus:ring-rose-500' : 
    'border-slate-300 dark:border-slate-600 focus:ring-emerald-500'
  }`}
/>
```

#### Design Guidelines

- **Base Style**: `w-full rounded-md border bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2`
- **Validation States**: Color-coded borders (emerald for valid, rose for invalid)
- **Focus Management**: Consistent ring styling with brand colors

---

### Progress Component

Visual progress indicators for multi-step processes.

```tsx
import { ProgressBar } from './components/ui/Progress';

<ProgressBar
  value={50}
  showLabel
  label="Profile Setup Progress"
  className="mb-2"
/>
```

---

## Animation Guidelines

### Transition Standards

All components use consistent transition timing:

```css
transition-all duration-300 ease-in-out
```

### Interactive Feedback

- **Buttons**: `active:scale-95` for click feedback
- **Cards**: `hover:translate-y-[1px]` for subtle movement
- **Focus States**: `focus:ring-2 focus:ring-emerald-500`

### Framer Motion Integration

For complex animations, use Framer Motion with consistent patterns:

```tsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.3 }}
>
  {content}
</motion.div>
```

## Accessibility Standards

### Color Contrast

All text meets WCAG AA standards (4.5:1 contrast ratio) through the carefully selected palette.

### Keyboard Navigation

- **Tab Order**: Natural DOM flow
- **Focus Management**: Visible focus rings on all interactive elements
- **Focus Trapping**: Implemented in modal dialogs

### ARIA Support

- **Button States**: `aria-pressed` for toggles
- **Form Labels**: `aria-describedby` for error messages
- **Live Regions**: `role="status"` for dynamic updates

## Dark Mode Support

All components support seamless dark mode through Tailwind's `dark:` prefixes:

```css
/* Light mode */
bg-white text-slate-900 border-slate-200

/* Dark mode */
dark:bg-slate-800 dark:text-slate-100 dark:border-slate-700
```

## Best Practices

### Component Composition

1. **Keep components focused** - Single responsibility principle
2. **Use consistent naming** - Follow established patterns
3. **Leverage design tokens** - Use predefined colors and spacing
4. **Maintain accessibility** - Always include proper ARIA attributes

### Performance Considerations

1. **Minimal re-renders** - Use React.memo where appropriate
2. **Lazy loading** - Load components as needed
3. **Optimized animations** - Use transform and opacity for smooth performance

### Responsive Design

1. **Mobile-first approach** - Start with mobile designs
2. **Breakpoint consistency** - Use Tailwind's standard breakpoints
3. **Touch-friendly targets** - Minimum 44px touch targets on mobile

## Development Workflow

### Adding New Components

1. Follow the established file structure in `ui/src/components/`
2. Implement with TypeScript for type safety
3. Include comprehensive prop documentation
4. Add Storybook stories for visual testing
5. Write unit tests for component logic
6. Update this documentation

### Testing Components

```bash
# Run component tests
npm run test

# Run visual regression tests
npm run test:visual

# Run accessibility tests
npm run test:a11y
```

This component library ensures consistency, maintainability, and accessibility across the entire Anghami-Spotify Migration Tool while providing a foundation for future development. 