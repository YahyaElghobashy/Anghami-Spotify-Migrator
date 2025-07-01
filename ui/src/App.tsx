import React, { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { AppLayout } from './components/layout/AppLayout';
import { SetupScreen } from './screens/SetupScreen';
import { UserProfileScreen } from './screens/UserProfileScreen';
import { AuthScreen } from './screens/AuthScreen';
import { ProfileInputScreen } from './screens/ProfileInputScreen';
import { Card, CardContent } from './components/ui/Card';
import { Button } from './components/ui/Button';
import { ProgressBar } from './components/ui/Progress';
import { Input } from './components/ui/Input';
import { Search, Music, Clock, PlayCircle } from 'lucide-react';
import { 
  apiClient, 
  checkBackendConnection, 
  loadUserPlaylists, 
  startPlaylistMigration,
  type AnghamiPlaylist,
  type MigrationStatus,
  type ProfileData,
  validateSession,
  logoutUser,
  // Add Spotify verification imports
  verifySpotifyAccount,
  getSpotifyProfile,
  type SpotifyUserProfile,
      type SpotifyVerificationResponse
} from './api/client';

// Application steps - Phase 0 added as first step
type AppStep = 'setup' | 'profile' | 'auth' | 'select' | 'migrate' | 'complete';
type AppScreen = AppStep | 'user-profile';

interface Playlist extends AnghamiPlaylist {
  isSelected: boolean;
}

// User session type
interface UserSession {
  user_id: string;
  session_token: string;
  display_name: string;
  spotify_client_id: string;
  created_at: string;
}

export const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState<AppStep>('setup');
  const [currentScreen, setCurrentScreen] = useState<AppScreen>('setup');
  const [userSession, setUserSession] = useState<UserSession | null>(null);
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [playlists, setPlaylists] = useState<Playlist[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [migrationProgress, setMigrationProgress] = useState(0);
  const [migrationStatus, setMigrationStatus] = useState<MigrationStatus | null>(null);
  const [migrationSessionId, setMigrationSessionId] = useState<string | null>(null);
  const [backendConnected, setBackendConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loading, setLoading] = useState(true);

  // Spotify verification state
  const [spotifyVerified, setSpotifyVerified] = useState(false);
  const [spotifyProfile, setSpotifyProfile] = useState<SpotifyUserProfile | null>(null);
  const [verificationLoading, setVerificationLoading] = useState(false);

  // Phase B.1: Navigation Enhancement - Step History and State Preservation
  const [stepHistory, setStepHistory] = useState<Array<{ step: AppStep, screen: AppScreen, timestamp: number }>>([]);
  const [navigationState, setNavigationState] = useState<{
    preservedSearchQuery?: string;
    preservedPlaylists?: Playlist[];
    preservedMigrationData?: any;
  }>({});

  // Enhanced navigation with history tracking
  const navigateToStep = (step: AppStep, screen?: AppScreen, preserveState: boolean = true) => {
    const targetScreen = screen || step;
    
    // Preserve current state if requested
    if (preserveState) {
      setNavigationState(prev => ({
        ...prev,
        preservedSearchQuery: searchQuery,
        preservedPlaylists: playlists,
        preservedMigrationData: migrationStatus ? {
          progress: migrationProgress,
          status: migrationStatus,
          sessionId: migrationSessionId
        } : undefined
      }));
    }

    // Add current step to history before navigating
    if (currentStep !== step || currentScreen !== targetScreen) {
      setStepHistory(prev => [
        ...prev.slice(-9), // Keep last 10 steps
        { 
          step: currentStep, 
          screen: currentScreen, 
          timestamp: Date.now() 
        }
      ]);
    }

    setCurrentStep(step);
    setCurrentScreen(targetScreen);
  };

  // Enhanced back navigation with state restoration
  const navigateBack = (_preserveCurrentState: boolean = false) => {
    if (stepHistory.length === 0) {
      // No history, go to setup
      navigateToStep('setup', 'setup', false);
      return;
    }

    // Get the last step from history
    const lastStep = stepHistory[stepHistory.length - 1];
    
    // Remove last step from history
    setStepHistory(prev => prev.slice(0, -1));

    // Restore state if available
    if (navigationState.preservedSearchQuery && (lastStep.step === 'select' || currentStep === 'select')) {
      setSearchQuery(navigationState.preservedSearchQuery);
    }
    
    if (navigationState.preservedPlaylists && (lastStep.step === 'select' || currentStep === 'select')) {
      setPlaylists(navigationState.preservedPlaylists);
    }

    if (navigationState.preservedMigrationData && lastStep.step === 'migrate') {
      setMigrationProgress(navigationState.preservedMigrationData.progress);
      setMigrationStatus(navigationState.preservedMigrationData.status);
      setMigrationSessionId(navigationState.preservedMigrationData.sessionId);
    }

    setCurrentStep(lastStep.step);
    setCurrentScreen(lastStep.screen);
  };

  // Check if back navigation is available
  const canNavigateBack = () => {
    return stepHistory.length > 0 || currentStep !== 'setup';
  };

  // Get step information for navigation
  const getStepInfo = (step: AppStep) => { // eslint-disable-line @typescript-eslint/no-unused-vars
    const stepMap = {
      setup: { title: 'Setup', description: 'Account setup', icon: '⚙️' },
      profile: { title: 'Profile', description: 'Anghami profile', icon: '👤' },
      auth: { title: 'Authentication', description: 'Connect Spotify', icon: '🔗' },
      select: { title: 'Select', description: 'Choose playlists', icon: '📋' },
      migrate: { title: 'Migration', description: 'Transfer playlists', icon: '⚡' },
      complete: { title: 'Complete', description: 'Migration finished', icon: '✅' }
    };
    return stepMap[step];
  };

  // Filter playlists based on search
  const filteredPlaylists = playlists.filter(playlist =>
    playlist.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    playlist.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const selectedPlaylists = playlists.filter(p => p.isSelected);

  // Check backend connection on app start
  useEffect(() => {
    const checkConnection = async () => {
      const connected = await checkBackendConnection();
      setBackendConnected(connected);
      
      if (!connected) {
        toast.error('Backend server not available. Please start the backend API server.');
      } else {
        toast.success('Connected to backend API server');
      }
    };
    
    checkConnection();
  }, []);

  // Check for existing session on app load
  useEffect(() => {
    const checkExistingSession = async () => {
      try {
        const savedSessionToken = localStorage.getItem('session_token');
        if (savedSessionToken) {
          const sessionValidation = await validateSession(savedSessionToken);
          if (sessionValidation.valid) {
            setUserSession(sessionValidation.session);
            // Load Spotify verification status
            await loadSpotifyProfile(sessionValidation.session.user_id);
            navigateToStep('profile', 'profile', false); // Skip setup if valid session exists
          } else {
            localStorage.removeItem('session_token');
          }
        }
      } catch (error) {
        console.warn('Session validation failed:', error);
        localStorage.removeItem('session_token');
      } finally {
        setLoading(false);
      }
    };

    checkExistingSession();
  }, []);

  // Handle successful setup completion
  const handleSetupComplete = async (session: UserSession) => {
    setUserSession(session);
    localStorage.setItem('session_token', session.session_token);
    // Load Spotify verification status for new session
    await loadSpotifyProfile(session.user_id);
    navigateToStep('profile');
  };

  // Handle successful profile confirmation
  const handleProfileConfirmed = (profile: ProfileData) => {
    setProfileData(profile);
    navigateToStep('auth');
  };

  // Handle logo click - go to home/setup
  const handleLogoClick = () => {
    // Clear all data when going home
    setProfileData(null);
    setPlaylists([]);
    setMigrationStatus(null);
    setMigrationSessionId(null);
    setStepHistory([]); // Clear navigation history
    navigateToStep('setup', 'setup', false);
  };

  // Handle profile click - go to user profile screen
  const handleProfileClick = () => {
    navigateToStep(currentStep, 'user-profile');
  };

  // Handle profile switch from user profile screen
  const handleProfileSwitch = async (session: UserSession) => {
    setUserSession(session);
    localStorage.setItem('session_token', session.session_token);
    setProfileData(null);
    // Load Spotify verification status for switched user
    await loadSpotifyProfile(session.user_id);
    navigateToStep('profile');
    toast.success(`Switched to ${session.display_name}'s account`);
  };

  // Handle back to app from user profile screen
  const handleBackToApp = () => {
    // Return to the previous step
    navigateBack();
  };

  // Handle logout
  const handleLogout = async () => {
    if (userSession) {
      try {
        await logoutUser(userSession.session_token);
      } catch (error) {
        console.warn('Logout API call failed:', error);
      }
    }
    
    setUserSession(null);
    setProfileData(null);
    setSpotifyVerified(false);
    setSpotifyProfile(null);
    localStorage.removeItem('session_token');
    setStepHistory([]); // Clear navigation history
    navigateToStep('setup', 'setup', false);
  };

  // Spotify verification functions
  const handleVerifySpotify = async () => {
    if (!userSession?.user_id) {
      toast.error('No active user session');
      return;
    }

    setVerificationLoading(true);
    try {
      const result = await verifySpotifyAccount(userSession.user_id);
      
      if (result.verified && result.spotify_profile) {
        setSpotifyVerified(true);
        setSpotifyProfile(result.spotify_profile);
        toast.success('Spotify account verified successfully!');
      } else {
        setSpotifyVerified(false);
        setSpotifyProfile(null);
        toast.error(result.error || 'Verification failed');
      }
    } catch (error) {
      console.error('Spotify verification error:', error);
      setSpotifyVerified(false);
      setSpotifyProfile(null);
    } finally {
      setVerificationLoading(false);
    }
  };

  // Load Spotify profile on session load
  const loadSpotifyProfile = async (userId: string) => {
    try {
      const profileResponse = await getSpotifyProfile(userId);
      
      if (profileResponse.verified && profileResponse.spotify_profile) {
        setSpotifyVerified(true);
        setSpotifyProfile(profileResponse.spotify_profile);
      } else {
        setSpotifyVerified(false);
        setSpotifyProfile(null);
      }
    } catch (error) {
      console.warn('Failed to load Spotify profile:', error);
      setSpotifyVerified(false);
      setSpotifyProfile(null);
    }
  };

  // Handle authentication completion
  const handleAuthComplete = async () => {
    setIsLoading(true);
    try {
      // For demo purposes, simulate successful authentication
      await apiClient.handleAuthCallback('demo_code', 'demo_state');
      
      // Load playlists after authentication
      const anghamiPlaylists = await loadUserPlaylists();
      const playlistsWithSelection = anghamiPlaylists.map(p => ({ ...p, isSelected: false }));
      setPlaylists(playlistsWithSelection);
      
      toast.success('Successfully authenticated with Spotify!');
      navigateToStep('select');
    } catch (error) {
      console.error('Authentication failed:', error);
      toast.error('Failed to connect. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlaylistToggle = (playlistId: string) => {
    setPlaylists(prev =>
      prev.map(playlist =>
        playlist.id === playlistId
          ? { ...playlist, isSelected: !playlist.isSelected }
          : playlist
      )
    );
  };

  const handleStartMigration = async () => {
    setIsLoading(true);
    try {
      const playlistIds = selectedPlaylists.map(p => p.id);
      const sessionId = await startPlaylistMigration(playlistIds);
      
      setMigrationSessionId(sessionId);
      navigateToStep('migrate');
      
      // Start polling for migration status
      startMigrationPolling(sessionId);
    } catch (error) {
      console.error('Failed to start migration:', error);
      toast.error('Failed to start migration. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Poll migration status
  const startMigrationPolling = (sessionId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await apiClient.getMigrationStatus(sessionId);
        setMigrationStatus(status);
        setMigrationProgress(status.progress);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setTimeout(() => {
            navigateToStep('complete');
          }, 1000);
        } else if (status.status === 'error') {
          clearInterval(pollInterval);
          toast.error(`Migration failed: ${status.message}`);
        }
      } catch (error) {
        console.error('Failed to get migration status:', error);
        clearInterval(pollInterval);
      }
    }, 1000);
  };

  // Navigation functions (Legacy - will be replaced with navigateBack)
  const handleBackToAuth = () => {
    setPlaylists([]);
    navigateToStep('auth');
  };

  const handleBackToSelect = () => { // eslint-disable-line @typescript-eslint/no-unused-vars
    setMigrationStatus(null);
    navigateToStep('select');
  };

  const handleBackToProfile = () => {
    setProfileData(null);
    navigateToStep('profile');
  };

  // Get current step number for progress display
  const getStepNumber = (): number => {
    switch (currentStep) {
      case 'setup': return 1;
      case 'profile': return 2;
      case 'auth': return 3;
      case 'select': return 4;
      case 'migrate': return 5;
      case 'complete': return 6;
      default: return 1;
    }
  };

  // Main steps data for progress display
  const steps = [ // eslint-disable-line @typescript-eslint/no-unused-vars
    { 
      title: 'Setup', 
      status: currentStep === 'setup' ? 'current' as const : (getStepNumber() > 0 ? 'completed' as const : 'pending' as const),
      description: userSession ? userSession.display_name : 'Account setup'
    },
    { 
      title: 'Profile Setup', 
      status: currentStep === 'profile' ? 'current' as const : (getStepNumber() > 1 ? 'completed' as const : 'pending' as const),
      description: profileData ? profileData.display_name || 'Profile confirmed' : 'Select profile'
    },
    { 
      title: 'Authentication', 
      status: currentStep === 'auth' ? 'current' as const : (getStepNumber() > 2 ? 'completed' as const : 'pending' as const),
      description: 'Connect Spotify account'
    },
    { 
      title: 'Select Playlists', 
      status: currentStep === 'select' ? 'current' as const : (getStepNumber() > 3 ? 'completed' as const : 'pending' as const),
      description: `${selectedPlaylists.length} selected`
    },
    { 
      title: 'Migration', 
      status: currentStep === 'migrate' ? 'current' as const : (getStepNumber() > 4 ? 'completed' as const : 'pending' as const),
      description: migrationStatus?.status || 'Ready to migrate'
    },
    { 
      title: 'Complete', 
      status: currentStep === 'complete' ? 'current' as const : 'pending' as const,
      description: 'Migration finished'
    }
  ];

  // Phase B.3: Handle step click navigation (for clickable progress steps)
  const handleStepClick = (stepNumber: number) => {
    const stepKeys: AppStep[] = ['setup', 'profile', 'auth', 'select', 'migrate', 'complete'];
    const targetStep = stepKeys[stepNumber - 1];
    
    // Only allow navigation to completed steps or current step
    if (stepNumber <= getStepNumber()) {
      navigateToStep(targetStep);
    }
  };

  const renderMainContent = () => {
    switch (currentScreen) {
      case 'setup':
        return <SetupScreen onSetupComplete={handleSetupComplete} />;

      case 'profile':
        return (
          <ProfileInputScreen 
            onProfileConfirmed={handleProfileConfirmed}
            onBack={canNavigateBack() ? navigateBack : undefined}
          />
        );

      case 'auth':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-display-sm font-extrabold text-slate-900 dark:text-slate-100 mb-2">
                  Connect Spotify
                </h1>
                <p className="text-lg text-slate-600 dark:text-slate-400">
                  Authorize access to create playlists in your Spotify account
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={handleBackToProfile}
                className="flex items-center space-x-2"
              >
                <span>← Change Profile</span>
              </Button>
            </div>
            <AuthScreen onAuthComplete={handleAuthComplete} />
          </div>
        );

      case 'select':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-display-sm font-extrabold text-slate-900 dark:text-slate-100 mb-2">
                  Select Playlists
                </h1>
                <p className="text-lg text-slate-600 dark:text-slate-400">
                  Choose which playlists you'd like to migrate to Spotify
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={handleBackToAuth}
                className="flex items-center space-x-2"
              >
                <span>← Back to Auth</span>
              </Button>
            </div>

            {/* Search */}
            <Card>
              <CardContent className="pt-6">
                <Input
                  leftIcon={<Search className="h-4 w-4" />}
                  placeholder="Search playlists..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </CardContent>
            </Card>

            {/* Playlists Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredPlaylists.map((playlist) => (
                <Card
                  key={playlist.id}
                  clickable
                  className={playlist.isSelected ? 'ring-2 ring-emerald-500' : ''}
                  onClick={() => handlePlaylistToggle(playlist.id)}
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start space-x-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-fuchsia-600 to-emerald-600 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Music className="h-8 w-8 text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate">
                          {playlist.name}
                        </h3>
                        {playlist.description && (
                          <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                            {playlist.description}
                          </p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
                          <div className="flex items-center space-x-1">
                            <PlayCircle className="h-4 w-4" />
                            <span>{playlist.trackCount} tracks</span>
                          </div>
                          <div className="flex items-center space-x-1">
                            <Clock className="h-4 w-4" />
                            <span>{playlist.duration}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex-shrink-0">
                        <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
                          playlist.isSelected 
                            ? 'bg-emerald-500 border-emerald-500' 
                            : 'border-slate-300 dark:border-slate-600'
                        }`}>
                          {playlist.isSelected && (
                            <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Action Buttons */}
            <div className="flex justify-between items-center">
              {playlists.length === 0 && backendConnected && (
                <Button
                  variant="secondary"
                  onClick={async () => {
                    setIsLoading(true);
                    try {
                      const anghamiPlaylists = await loadUserPlaylists();
                      const playlistsWithSelection = anghamiPlaylists.map(p => ({ ...p, isSelected: false }));
                      setPlaylists(playlistsWithSelection);
                    } catch (error) {
                      console.error('Failed to load playlists:', error);
                    } finally {
                      setIsLoading(false);
                    }
                  }}
                  loading={isLoading}
                >
                  Load Playlists
                </Button>
              )}
              
              {selectedPlaylists.length > 0 && (
                <div className="ml-auto">
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleStartMigration}
                    disabled={!backendConnected}
                    loading={isLoading}
                    className="flex items-center space-x-2"
                  >
                    <span>Start Migration</span>
                    <span className="text-sm">({selectedPlaylists.length} playlists)</span>
                  </Button>
                </div>
              )}
            </div>
          </div>
        );

      case 'migrate':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-display-sm font-extrabold text-slate-900 dark:text-slate-100 mb-2">
                Migrating Playlists
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-400">
                Please wait while we transfer your playlists to Spotify
              </p>
            </div>

            <Card>
              <CardContent className="pt-6">
                <ProgressBar
                  value={migrationProgress}
                  showLabel
                  label="Migration Progress"
                  size="lg"
                />
                <div className="mt-4 space-y-2">
                  <div className="text-center">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {migrationStatus?.message || 'Processing...'}
                    </p>
                  </div>
                  
                  {migrationStatus && (
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="text-center">
                        <div className="font-medium text-slate-900 dark:text-slate-100">
                          {migrationStatus.matchedTracks} / {migrationStatus.totalTracks}
                        </div>
                        <div className="text-slate-500 dark:text-slate-400">Tracks Matched</div>
                      </div>
                      <div className="text-center">
                        <div className="font-medium text-slate-900 dark:text-slate-100">
                          {migrationStatus.completedPlaylists} / {migrationStatus.totalPlaylists}
                        </div>
                        <div className="text-slate-500 dark:text-slate-400">Playlists Created</div>
                      </div>
                    </div>
                  )}
                  
                  {migrationStatus?.currentPlaylist && (
                    <div className="text-center">
                      <p className="text-xs text-slate-500 dark:text-slate-400">
                        Current: {migrationStatus.currentPlaylist}
                      </p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        );

      case 'complete':
        return (
          <div className="space-y-6 text-center">
            <div>
              <div className="mx-auto w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center mb-4">
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
              <h1 className="text-display-sm font-extrabold text-slate-900 dark:text-slate-100 mb-2">
                Migration Complete!
              </h1>
              <p className="text-lg text-slate-600 dark:text-slate-400">
                Your playlists have been successfully transferred to Spotify
              </p>
            </div>

            <Card>
              <CardContent className="pt-6">
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    Migration Summary
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-2xl font-bold text-emerald-600">
                        {migrationStatus?.createdPlaylists || selectedPlaylists.length}
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">
                        Playlists Migrated
                      </div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-emerald-600">
                        {migrationStatus?.matchedTracks || selectedPlaylists.reduce((sum, p) => sum + p.trackCount, 0)}
                      </div>
                      <div className="text-sm text-slate-600 dark:text-slate-400">
                        Tracks Transferred
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex space-x-4 justify-center">
              <Button
                variant="primary"
                size="lg"
                onClick={() => window.open('https://open.spotify.com', '_blank')}
              >
                Open Spotify
              </Button>
              <Button
                variant="secondary"
                size="lg"
                onClick={() => {
                  setProfileData(null);
                  setPlaylists([]);
                  setMigrationStatus(null);
                  setMigrationSessionId(null);
                  navigateToStep('profile', 'profile', false);
                }}
              >
                Start New Migration
              </Button>
            </div>
          </div>
        );

      case 'user-profile':
        return (
          <UserProfileScreen
            currentSession={userSession}
            onProfileSwitch={handleProfileSwitch}
            onBackToApp={handleBackToApp}
            onLogout={handleLogout}
          />
        );

      default:
        return null;
    }
  };

  // Show loading screen while checking session
  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-fuchsia-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl font-bold text-white">🎵</span>
          </div>
          <p className="text-slate-600 dark:text-slate-400">Loading...</p>
        </div>
      </div>
    );
  }

  // Phase 0: Setup Screen (before main app layout)
  if (currentScreen === 'setup') {
    return (
      <>
        <SetupScreen onSetupComplete={handleSetupComplete} />
        <Toaster position="top-right" />
      </>
    );
  }

  // User Profile Management Screen
  if (currentScreen === 'user-profile') {
    return (
      <>
        <UserProfileScreen
          currentSession={userSession}
          onProfileSwitch={handleProfileSwitch}
          onBackToApp={handleBackToApp}
          onLogout={handleLogout}
        />
        <Toaster position="top-right" />
      </>
    );
  }

  // Main app with layout
  return (
    <>
      <AppLayout
        currentStep={getStepNumber()}
        totalSteps={6}
        userSession={userSession ? {
          ...userSession,
          avatar_url: profileData?.avatar_url // Include avatar from profile data
        } : undefined}
        onLogoClick={handleLogoClick}
        onProfileClick={handleProfileClick}
        onLogout={handleLogout}
        // Enhanced Navigation Props
        canNavigateBack={canNavigateBack()}
        onBackClick={navigateBack}
        onStepClick={handleStepClick}
        stepHistory={stepHistory}
        // New screen transition props
        screenKey={currentScreen}
        showTimeline={!['setup', 'profile', 'user-profile'].includes(currentScreen)}
        // Spotify verification props
        spotifyVerified={spotifyVerified}
        spotifyProfile={spotifyProfile || undefined}
        onVerifySpotify={handleVerifySpotify}
      >
        {renderMainContent()}
      </AppLayout>
      <Toaster position="top-right" />
    </>
  );
}; 