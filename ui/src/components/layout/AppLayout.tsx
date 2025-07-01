import React from 'react';
import { clsx } from 'clsx';
import { SiSpotify } from 'react-icons/si';
import { User, ChevronDown, CheckCircle, XCircle, Shield } from 'lucide-react';
import { Button } from '../ui/Button';
import { Timeline, TimelineStep } from '../ui/Timeline';
import { ScreenTransition } from '../ui/ScreenTransition';
import AnghamiIcon from '../../assets/anghami-icon.svg';
import AnghamiIconPng from '../../assets/anghami-icon.png';
import AnghamiLogo from '../../assets/anghami-logo.svg';

// Import types for Spotify verification
interface SpotifyProfile {
  spotify_id: string;
  display_name: string;
  email?: string;
  avatar_url?: string;
  follower_count?: number;
  country?: string;
  subscription_type?: string;
  verified: boolean;
}

export interface AppLayoutProps {
  children: React.ReactNode;
  currentStep?: number;
  totalSteps?: number;
  className?: string;
  userSession?: any;
  onLogoClick?: () => void;
  onProfileClick?: () => void;
  onLogout?: () => void;
  // Enhanced Navigation Props
  canNavigateBack?: boolean;
  onBackClick?: () => void;
  onStepClick?: (stepNumber: number) => void;
  stepHistory?: Array<{ step: string, screen: string, timestamp: number }>;
  // New props for screen transitions
  screenKey?: string;
  showTimeline?: boolean;
  // Spotify verification props
  spotifyVerified?: boolean;
  spotifyProfile?: SpotifyProfile;
  onVerifySpotify?: () => void;
}

const steps = [
  { 
    id: 1, 
    name: 'Setup', 
    description: 'Account setup', 
    key: 'setup',
    details: 'Configure your migration settings and create your account'
  },
  { 
    id: 2, 
    name: 'Profile', 
    description: 'Anghami profile', 
    key: 'profile',
    details: 'Connect and validate your Anghami profile for playlist access'
  },
  { 
    id: 3, 
    name: 'Authenticate', 
    description: 'Connect Spotify', 
    key: 'auth',
    details: 'Authorize Spotify access to create playlists in your account'
  },
  { 
    id: 4, 
    name: 'Select', 
    description: 'Choose playlists', 
    key: 'select',
    details: 'Browse and select which playlists you want to migrate'
  },
  { 
    id: 5, 
    name: 'Migrate', 
    description: 'Transfer to Spotify', 
    key: 'migrate',
    details: 'Transfer your selected playlists and tracks to Spotify'
  },
  { 
    id: 6, 
    name: 'Complete', 
    description: 'Migration summary', 
    key: 'complete',
    details: 'Review successful migrations and any issues encountered'
  },
];

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  currentStep = 1,
  totalSteps = 6, // eslint-disable-line @typescript-eslint/no-unused-vars
  className,
  userSession,
  onLogoClick,
  onProfileClick,
  onLogout, // eslint-disable-line @typescript-eslint/no-unused-vars
  canNavigateBack,
  onBackClick,
  onStepClick,
  stepHistory, // eslint-disable-line @typescript-eslint/no-unused-vars
  screenKey = 'default',
  showTimeline = true,
  spotifyVerified,
  spotifyProfile,
  onVerifySpotify,
}) => {
  // Convert steps to TimelineStep format with status
  const timelineSteps: TimelineStep[] = steps.map(step => ({
    ...step,
    status: step.id < currentStep ? 'completed' : 
            step.id === currentStep ? 'current' : 'pending'
  }));

  return (
    <div className={clsx('flex flex-col min-h-screen bg-slate-50 dark:bg-slate-900', className)}>
      {/* Simplified Clean Header */}
      <header className="bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 sticky top-0 z-40">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            
            {/* Left Section - Back Navigation */}
            <div className="flex items-center space-x-4">
              {/* Clean Back Navigation Button */}
              {canNavigateBack && onBackClick && (
                <button
                  onClick={onBackClick}
                  className="inline-flex items-center px-3 py-2 rounded-md bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back
                </button>
              )}
            </div>

            {/* Center Section - Clean Logo Design */}
            <div className="flex items-center">
              <button
                onClick={onLogoClick}
                className="flex items-center space-x-3 hover:opacity-80 transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500 rounded-md px-2 py-1"
              >
                <div className="flex items-center space-x-2">
                  {/* Official Anghami Icon with PNG fallback */}
                  <img 
                    src={AnghamiIcon} 
                    alt="Anghami" 
                    className="w-8 h-8 rounded-md"
                    onError={(e) => {
                      // Fallback to PNG version if SVG fails
                      const target = e.target as HTMLImageElement;
                      target.src = AnghamiIconPng;
                    }}
                  />
                  {/* Arrow */}
                  <svg className="w-4 h-4 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  {/* Spotify Icon */}
                  <div className="w-8 h-8 bg-emerald-600 rounded-md flex items-center justify-center">
                    <SiSpotify className="h-5 w-5 text-white" />
                  </div>
                </div>
                <div className="hidden sm:block">
                  {/* Official Anghami Logo with enhanced styling for black text */}
                  <div className="flex items-center space-x-2">
                    <img 
                      src={AnghamiLogo} 
                      alt="Anghami" 
                      className="h-6 dark:invert dark:brightness-0 dark:contrast-100"
                      style={{ filter: 'brightness(0.2)' }}
                    />
                    <span className="text-slate-600 dark:text-slate-300 text-sm font-medium">
                      → Spotify Migration
                    </span>
                  </div>
                </div>
              </button>
            </div>

            {/* Right Section - User Profile */}
            <div className="flex items-center space-x-4">
              {/* Clean User Profile */}
              {userSession && (
                <div className="relative">
                  <Button
                    onClick={onProfileClick}
                    variant="ghost"
                    className="flex items-center space-x-2 px-3 py-2"
                  >
                    {/* User Avatar - Now displays actual image */}
                    <div className="w-8 h-8 rounded-full flex items-center justify-center overflow-hidden flex-shrink-0">
                      {/* Show Spotify avatar if verified and available, otherwise Anghami avatar */}
                      {spotifyVerified && spotifyProfile?.avatar_url ? (
                        <img
                          src={spotifyProfile.avatar_url}
                          alt={`${spotifyProfile.display_name || 'Spotify User'}'s avatar`}
                          className="w-full h-full object-cover rounded-full"
                          onError={(e) => {
                            // Fallback to Anghami avatar or icon if Spotify image fails
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent && userSession.avatar_url) {
                              parent.innerHTML = `<img src="${userSession.avatar_url}" alt="Anghami avatar" class="w-full h-full object-cover rounded-full" />`;
                            } else if (parent) {
                              parent.classList.add('bg-fuchsia-600');
                              parent.innerHTML = '<svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
                            }
                          }}
                        />
                      ) : userSession.avatar_url ? (
                        <img
                          src={userSession.avatar_url}
                          alt={`${userSession.display_name || 'User'}'s avatar`}
                          className="w-full h-full object-cover rounded-full"
                          onError={(e) => {
                            // Fallback to icon if image fails to load
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent) {
                              parent.classList.add('bg-fuchsia-600');
                              parent.innerHTML = '<svg class="h-4 w-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
                            }
                          }}
                        />
                      ) : (
                        <div className="w-full h-full bg-fuchsia-600 rounded-full flex items-center justify-center">
                          <User className="h-4 w-4 text-white" />
                        </div>
                      )}
                    </div>
                    <div className="hidden sm:block text-left">
                      {/* User Display Name with Verification Badge */}
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-medium text-slate-900 dark:text-slate-100">
                          {userSession.display_name}
                        </p>
                        {/* Verification Badge */}
                        {spotifyVerified ? (
                          <div title="Spotify Verified">
                            <CheckCircle className="h-4 w-4 text-blue-500" />
                          </div>
                        ) : (
                          <div className="flex items-center space-x-1">
                            <div title="Spotify Not Verified">
                              <XCircle className="h-3 w-3 text-amber-500" />
                            </div>
                            {onVerifySpotify && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onVerifySpotify();
                                }}
                                className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                                title="Click to verify Spotify account"
                              >
                                Verify
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                      {/* Connection Status with Spotify details if verified */}
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        {spotifyVerified ? (
                          <span className="flex items-center space-x-1">
                            <SiSpotify className="h-3 w-3 text-emerald-600" />
                            <span>{spotifyProfile?.subscription_type || 'Spotify'} • Verified</span>
                          </span>
                        ) : (
                          'Connected'
                        )}
                      </p>
                    </div>
                    <ChevronDown className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                  </Button>
                  
                  {/* Verification Status Indicator for Mobile */}
                  <div className="sm:hidden absolute -top-1 -right-1">
                    {spotifyVerified ? (
                      <CheckCircle className="h-4 w-4 text-blue-500 bg-white dark:bg-slate-800 rounded-full" />
                    ) : (
                      <div className="h-4 w-4 bg-amber-500 rounded-full flex items-center justify-center">
                        <Shield className="h-2 w-2 text-white" />
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content with timeline */}
      <main className="flex-1 container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className={clsx(
          'grid gap-8',
          showTimeline ? 'grid-cols-1 lg:grid-cols-[1fr_320px]' : 'grid-cols-1'
        )}>
          
          {/* Primary content with screen transitions */}
          <div className="min-w-0">
            <ScreenTransition screenKey={screenKey}>
              {children}
            </ScreenTransition>
          </div>

          {/* Timeline Sidebar */}
          {showTimeline && (
            <aside className="lg:sticky lg:top-24 lg:self-start">
              <div className="bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm p-6">
                <Timeline
                  steps={timelineSteps}
                  currentStep={currentStep}
                  onStepClick={onStepClick}
                />
              </div>
            </aside>
          )}
        </div>
      </main>

      {/* Clean Footer */}
      <footer className="bg-white dark:bg-slate-800 border-t border-slate-200 dark:border-slate-700">
        <div className="container mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between space-y-2 sm:space-y-0">
            <div className="flex items-center space-x-4 text-sm text-slate-500 dark:text-slate-400">
              <div className="flex items-center space-x-2">
                <img 
                  src={AnghamiIcon} 
                  alt="Anghami" 
                  className="w-4 h-4 rounded-sm"
                />
                <span>Anghami</span>
              </div>
              <span>→</span>
              <div className="flex items-center space-x-2">
                <SiSpotify className="w-4 h-4 text-emerald-600" />
                <span>Spotify</span>
              </div>
            </div>
            <div className="text-sm text-slate-500 dark:text-slate-400">
              Migration Tool v2.0.0
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}; 