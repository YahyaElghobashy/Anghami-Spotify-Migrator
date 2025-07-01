import { toast } from 'react-hot-toast';

// API Configuration
const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  ENDPOINTS: {
    AUTH: '/auth/spotify',
    AUTH_STATUS: '/auth/status',
    PLAYLISTS: '/playlists',
    MIGRATE: '/migrate',
    STATUS: '/migrate/status',
    HEALTH: '/health',
    // Profile Management Endpoints
    PROFILE_VALIDATE: '/profiles/validate',
    PROFILE_HISTORY: '/profiles/history',
    PROFILE_CONFIRM: '/profiles/confirm'
  }
};

// Types
export interface AnghamiPlaylist {
  id: string;
  name: string;
  trackCount: number;
  duration: string;
  description?: string;
  imageUrl?: string;
  tracks?: AnghamiTrack[];
}

export interface AnghamiTrack {
  id: string;
  title: string;
  artist: string;
  album?: string;
  duration?: string;
  confidence?: number;
  spotifyMatch?: {
    id: string;
    name: string;
    artist: string;
    confidence: number;
  };
}

export interface MigrationStatus {
  sessionId: string;
  status: 'idle' | 'extracting' | 'matching' | 'creating' | 'completed' | 'error';
  progress: number;
  currentPlaylist?: string;
  totalPlaylists: number;
  completedPlaylists: number;
  totalTracks: number;
  matchedTracks: number;
  createdPlaylists: number;
  errors: string[];
  message?: string;
}

export interface AuthStatus {
  authenticated: boolean;
  user?: {
    id: string;
    name: string;
    email?: string;
    profile_url?: string;
  };
  expiresAt?: string;
}

// Profile Management Types
export interface ProfileData {
  profile_url: string;
  display_name?: string;
  avatar_url?: string;
  follower_count?: number;
  is_valid: boolean;
  error_message?: string;
}

export interface ProfileHistoryItem {
  id: number;
  profile_url: string;
  display_name?: string;
  avatar_url?: string;
  follower_count?: number;
  usage_count: number;
  last_used: string;
}

export interface ProfileValidationRequest {
  profile_url: string;
}

// User setup and session management types
interface UserSetupRequest {
  spotify_client_id: string;
  spotify_client_secret: string;
  display_name?: string;
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
interface UserSession {
  user_id: string;
  session_token: string;
  display_name: string;
  spotify_client_id: string;
  created_at: string;
}

interface UserCredentials {
  user_id: string;
  display_name: string;
  spotify_client_id: string;
  has_credentials: boolean;
  created_at: string;
  last_used?: string;
}

// Spotify verification types
interface SpotifyUserProfile {
  spotify_id: string;
  display_name: string;
  email?: string;
  avatar_url?: string;
  follower_count?: number;
  country?: string;
  subscription_type?: string;
  verified: boolean;
}

interface SpotifyVerificationResponse {
  verified: boolean;
  spotify_profile?: SpotifyUserProfile;
  message?: string;
  error?: string;
}

interface SpotifyProfileResponse {
  verified: boolean;
  spotify_profile?: SpotifyUserProfile;
  last_verification?: string;
}

// API Client Class
class APIClient {
  private baseURL: string;

  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
      },
      ...options,
    };

    try {
      const response = await fetch(url, defaultOptions);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      
      if (error instanceof Error) {
        toast.error(`API Error: ${error.message}`);
        throw error;
      }
      
      toast.error('An unexpected error occurred');
      throw new Error('Network error occurred');
    }
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request(API_CONFIG.ENDPOINTS.HEALTH);
  }

  // Profile Management
  async validateProfile(profileUrl: string): Promise<ProfileData> {
    return this.request(API_CONFIG.ENDPOINTS.PROFILE_VALIDATE, {
      method: 'POST',
      body: JSON.stringify({ profile_url: profileUrl }),
    });
  }

  async getProfileHistory(): Promise<ProfileHistoryItem[]> {
    return this.request(API_CONFIG.ENDPOINTS.PROFILE_HISTORY);
  }

  async confirmProfile(profileUrl: string): Promise<ProfileData> {
    return this.request(API_CONFIG.ENDPOINTS.PROFILE_CONFIRM, {
      method: 'POST',
      body: JSON.stringify({ profile_url: profileUrl }),
    });
  }

  async deleteProfileFromHistory(profileId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/profiles/${profileId}`, {
      method: 'DELETE',
    });
  }

  // Authentication
  async authenticateSpotify(): Promise<{ authUrl: string }> {
    return this.request(API_CONFIG.ENDPOINTS.AUTH, {
      method: 'POST',
    });
  }

  async getAuthStatus(): Promise<AuthStatus> {
    return this.request(API_CONFIG.ENDPOINTS.AUTH_STATUS);
  }

  async handleAuthCallback(code: string, state: string): Promise<AuthStatus> {
    return this.request('/auth/callback', {
      method: 'POST',
      body: JSON.stringify({ code, state }),
    });
  }

  // Playlists
  async getPlaylists(): Promise<AnghamiPlaylist[]> {
    return this.request(API_CONFIG.ENDPOINTS.PLAYLISTS);
  }

  async getPlaylistDetails(playlistId: string): Promise<AnghamiPlaylist> {
    return this.request(`${API_CONFIG.ENDPOINTS.PLAYLISTS}/${playlistId}`);
  }

  // Migration
  async startMigration(playlistIds: string[]): Promise<{ sessionId: string }> {
    return this.request(API_CONFIG.ENDPOINTS.MIGRATE, {
      method: 'POST',
      body: JSON.stringify({ playlist_ids: playlistIds }),
    });
  }

  async getMigrationStatus(sessionId: string): Promise<MigrationStatus> {
    return this.request(`${API_CONFIG.ENDPOINTS.STATUS}/${sessionId}`);
  }

  async stopMigration(sessionId: string): Promise<{ success: boolean }> {
    return this.request(`${API_CONFIG.ENDPOINTS.MIGRATE}/${sessionId}/stop`, {
      method: 'POST',
    });
  }

  // Spotify Verification
  async verifySpotifyAccount(userId: string): Promise<SpotifyVerificationResponse> {
    return this.request('/spotify/verify', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async getSpotifyProfile(userId: string): Promise<SpotifyProfileResponse> {
    return this.request(`/spotify/profile/${userId}`);
  }

  // WebSocket connection for real-time updates
  createWebSocket(sessionId: string): WebSocket {
    const wsUrl = API_CONFIG.BASE_URL.replace('http', 'ws') + `/ws/${sessionId}`;
    return new WebSocket(wsUrl);
  }
}

// Export singleton instance
export const apiClient = new APIClient();

// Utility functions for common operations
export async function checkBackendConnection(): Promise<boolean> {
  try {
    await apiClient.healthCheck();
    return true;
  } catch (error) {
    console.error('Backend connection failed:', error);
    return false;
  }
}

// Profile Management Utilities
export async function validateAnghamiProfile(profileUrl: string): Promise<ProfileData> {
  try {
    toast.loading('Validating profile...', { id: 'profile-validation' });
    const profileData = await apiClient.validateProfile(profileUrl);
    
    if (profileData.is_valid) {
      toast.success('Profile validated successfully!', { id: 'profile-validation' });
    } else {
      toast.error(profileData.error_message || 'Profile validation failed', { id: 'profile-validation' });
    }
    
    return profileData;
  } catch (error) {
    toast.error('Failed to validate profile', { id: 'profile-validation' });
    throw error;
  }
}

export async function loadProfileHistory(): Promise<ProfileHistoryItem[]> {
  try {
    const history = await apiClient.getProfileHistory();
    return history;
  } catch (error) {
    console.error('Failed to load profile history:', error);
    return [];
  }
}

export async function confirmAnghamiProfile(profileUrl: string): Promise<ProfileData> {
  try {
    toast.loading('Confirming profile...', { id: 'profile-confirmation' });
    const profileData = await apiClient.confirmProfile(profileUrl);
    
    if (profileData.is_valid) {
      toast.success(`Welcome, ${profileData.display_name || 'Anghami User'}!`, { id: 'profile-confirmation' });
    } else {
      toast.error('Profile confirmation failed', { id: 'profile-confirmation' });
    }
    
    return profileData;
  } catch (error) {
    toast.error('Failed to confirm profile', { id: 'profile-confirmation' });
    throw error;
  }
}

// Authentication Utilities
export async function initializeAuth(): Promise<string> {
  try {
    // Check if already authenticated
    const authStatus = await apiClient.getAuthStatus();
    if (authStatus.authenticated) {
      toast.success(`Welcome back, ${authStatus.user?.name || 'User'}!`);
      return 'authenticated';
    }

    // Start authentication flow
    const { authUrl } = await apiClient.authenticateSpotify();
    window.location.href = authUrl;
    return 'redirecting';
  } catch (error) {
    toast.error('Failed to initialize authentication');
    throw error;
  }
}

export async function loadUserPlaylists(): Promise<AnghamiPlaylist[]> {
  try {
    toast.loading('Loading your Anghami playlists...', { id: 'loading-playlists' });
    const playlists = await apiClient.getPlaylists();
    toast.success(`Found ${playlists.length} playlists`, { id: 'loading-playlists' });
    return playlists;
  } catch (error) {
    toast.error('Failed to load playlists', { id: 'loading-playlists' });
    throw error;
  }
}

export async function startPlaylistMigration(playlistIds: string[]): Promise<string> {
  try {
    toast.loading('Starting migration...', { id: 'migration-start' });
    const { sessionId } = await apiClient.startMigration(playlistIds);
    toast.success('Migration started successfully!', { id: 'migration-start' });
    return sessionId;
  } catch (error) {
    toast.error('Failed to start migration', { id: 'migration-start' });
    throw error;
  }
}

// Phase 0: User Setup and Session Management

export async function createUser(request: UserSetupRequest) {
  const response = await fetch(`${API_CONFIG.BASE_URL}/setup/create-user`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function loginUser(userId: string) {
  const response = await fetch(`${API_CONFIG.BASE_URL}/setup/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function validateSession(sessionToken: string) {
  const response = await fetch(`${API_CONFIG.BASE_URL}/setup/session/${sessionToken}`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function logoutUser(sessionToken: string) {
  const response = await fetch(`${API_CONFIG.BASE_URL}/setup/logout`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_token: sessionToken }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

export async function listUsers(): Promise<UserCredentials[]> {
  const response = await fetch(`${API_CONFIG.BASE_URL}/setup/users`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  const data = await response.json();
  return data.users || [];
}

export async function getUserCredentials(userId: string) {
  const response = await fetch(`${API_CONFIG.BASE_URL}/setup/user/${userId}/credentials`);

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// Spotify Verification Utilities
export async function verifySpotifyAccount(userId: string): Promise<SpotifyVerificationResponse> {
  try {
    toast.loading('Verifying Spotify account...', { id: 'spotify-verification' });
    const result = await apiClient.verifySpotifyAccount(userId);
    
    if (result.verified) {
      toast.success(result.message || 'Spotify account verified successfully!', { id: 'spotify-verification' });
    } else {
      toast.error(result.error || 'Spotify verification failed', { id: 'spotify-verification' });
    }
    
    return result;
  } catch (error) {
    toast.error('Failed to verify Spotify account', { id: 'spotify-verification' });
    throw error;
  }
}

export async function getSpotifyProfile(userId: string): Promise<SpotifyProfileResponse> {
  try {
    const profile = await apiClient.getSpotifyProfile(userId);
    return profile;
  } catch (error) {
    console.error('Failed to get Spotify profile:', error);
    return { verified: false, spotify_profile: undefined, last_verification: undefined };
  }
}

// Export types for external use
export type { SpotifyUserProfile, SpotifyVerificationResponse, SpotifyProfileResponse }; 