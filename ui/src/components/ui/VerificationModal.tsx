import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  X, 
  CheckCircle, 
  AlertCircle, 
  RefreshCw, 
  User, 
  Globe, 
  Music, 
  Clock, 
  ExternalLink,
  Shield,
  Crown,
  Calendar,
  Headphones
} from 'lucide-react';
import { SiSpotify } from 'react-icons/si';
import { Button } from './Button';
import { Card, CardContent, CardHeader } from './Card';
import { toast } from 'react-hot-toast';
import { 
  getDetailedSpotifyProfile, 
  getRecentlyPlayedTracks, 
  refreshSpotifyConnection,
  startSpotifyOAuth,
  type SpotifyFullProfile,
  type SpotifyRecentlyPlayed
} from '../../api/client';

interface VerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  userId: string;
  initialProfile?: SpotifyFullProfile;
  onProfileUpdate?: (profile: SpotifyFullProfile) => void;
}

export const VerificationModal: React.FC<VerificationModalProps> = ({
  isOpen,
  onClose,
  userId,
  initialProfile,
  onProfileUpdate
}) => {
  const [profile, setProfile] = useState<SpotifyFullProfile | null>(initialProfile || null);
  const [recentlyPlayed, setRecentlyPlayed] = useState<SpotifyRecentlyPlayed[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>('');
  const [isStartingOAuth, setIsStartingOAuth] = useState(false);
  const [needsRealVerification, setNeedsRealVerification] = useState(false);

  useEffect(() => {
    if (isOpen && userId) {
      loadVerificationData();
    }
  }, [isOpen, userId]);

  const loadVerificationData = async () => {
    if (!userId) {
      console.warn('No user ID provided for verification modal');
      return;
    }
    
    setIsLoading(true);
    try {
      // First check detailed profile status
      const detailedResponse = await getDetailedSpotifyProfile(userId);
      
      if (detailedResponse.verified && detailedResponse.spotify_profile) {
        setProfile(detailedResponse.spotify_profile);
        setLastUpdated(detailedResponse.last_verification || 'Unknown');
        
        // Check if we have real-time connection
        if (detailedResponse.connection_status === 'active') {
          // Try to load recently played tracks
          try {
            const tracksResponse = await getRecentlyPlayedTracks(userId);
            if (tracksResponse.success) {
              setRecentlyPlayed(tracksResponse.recently_played);
            }
          } catch (error) {
            console.warn('Failed to load recently played tracks:', error);
          }
        } else {
          // Connection is not active - need OAuth
          setNeedsRealVerification(true);
        }
      } else {
        // No verification at all - definitely need OAuth
        setNeedsRealVerification(true);
      }
    } catch (error) {
      console.error('Failed to load verification data:', error);
      setNeedsRealVerification(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRefreshConnection = async () => {
    setIsRefreshing(true);
    try {
      const result = await refreshSpotifyConnection(userId);

      if (result.verified) {
        let updatedProfile = result.spotify_profile;

        // If API did not return the updated profile, fetch it manually
        if (!updatedProfile) {
          const profileResponse = await getDetailedSpotifyProfile(userId);
          if (profileResponse.verified && profileResponse.spotify_profile) {
            updatedProfile = profileResponse.spotify_profile;
          }
        }

        if (updatedProfile) {
          setProfile(updatedProfile);
          setLastUpdated(new Date().toISOString());
          onProfileUpdate?.(updatedProfile);

          // Reload recently played tracks
          try {
            const tracksResponse = await getRecentlyPlayedTracks(userId);
            if (tracksResponse.success) {
              setRecentlyPlayed(tracksResponse.recently_played);
            }
          } catch (error) {
            console.warn('Failed to reload recently played tracks:', error);
          }
        }
      }
    } catch (error) {
      console.error('Failed to refresh connection:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleReauthorize = async () => {
    try {
      const authUrl = await startSpotifyOAuth(userId);
      if (authUrl) {
        window.open(authUrl, '_blank', 'width=600,height=700');
      }
    } catch (error) {
      console.error('Failed to start OAuth:', error);
    }
  };

  const formatLastPlayed = (playedAt: string) => {
    try {
      const date = new Date(playedAt);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      
      if (diffHours > 24) {
        return date.toLocaleDateString();
      } else if (diffHours > 0) {
        return `${diffHours}h ago`;
      } else {
        return `${diffMinutes}m ago`;
      }
    } catch {
      return playedAt;
    }
  };

  const getConnectionStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-emerald-600';
      case 'expired':
      case 'token_expired':
        return 'text-amber-600';
      case 'invalid': return 'text-red-600';
      default: return 'text-slate-600';
    }
  };

  const getConnectionStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <CheckCircle className="h-4 w-4 text-emerald-600" />;
      case 'expired':
      case 'token_expired':
        return <AlertCircle className="h-4 w-4 text-amber-600" />;
      case 'invalid': return <AlertCircle className="h-4 w-4 text-red-600" />;
      default: return <Shield className="h-4 w-4 text-slate-600" />;
    }
  };

  const formatConnectionStatus = (status: string) => {
    switch (status) {
      case 'active':
        return 'Running';
      case 'expired':
      case 'token_expired':
        return 'Token Expired';
      case 'invalid':
        return 'Connection Invalid';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  const startOAuthVerification = async () => {
    setIsStartingOAuth(true);
    try {
      const response = await startSpotifyOAuth(userId);
      if (response) {
        // Open Spotify OAuth in a new window
        const authWindow = window.open(
          response,
          'spotify-auth',
          'width=500,height=600,scrollbars=yes,resizable=yes'
        );

        // Listen for OAuth completion
        const checkAuthWindow = setInterval(() => {
          try {
            if (authWindow?.closed) {
              clearInterval(checkAuthWindow);
              // Refresh verification data
              setTimeout(() => {
                loadVerificationData();
              }, 1000);
            }
          } catch (error) {
            // Window might be blocked by CORS
            clearInterval(checkAuthWindow);
          }
        }, 1000);

        // Auto-close after 5 minutes
        setTimeout(() => {
          if (authWindow && !authWindow.closed) {
            authWindow.close();
          }
          clearInterval(checkAuthWindow);
        }, 300000);
        
      } else {
        throw new Error('Failed to start OAuth');
      }
    } catch (error) {
      console.error('OAuth error:', error);
    } finally {
      setIsStartingOAuth(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white dark:bg-slate-800 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-700">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-emerald-100 dark:bg-emerald-900 rounded-lg">
              <SiSpotify className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Spotify Account Verification
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Complete verification details and connection status
              </p>
            </div>
          </div>
          <Button
            onClick={onClose}
            variant="ghost"
            className="p-2"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
              <span className="ml-3 text-slate-600 dark:text-slate-400">Loading verification details...</span>
            </div>
          ) : needsRealVerification ? (
            <div className="text-center py-8">
              <Shield className="h-12 w-12 text-amber-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2 text-slate-900 dark:text-slate-100">
                Real-time Verification Required
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-6">
                To verify your Spotify connection and access real-time data, 
                you need to authorize this application with your Spotify account.
              </p>
              <Button
                onClick={startOAuthVerification}
                disabled={isStartingOAuth}
                className="bg-green-500 hover:bg-green-600 text-white"
              >
                {isStartingOAuth ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    Starting Authorization...
                  </>
                ) : (
                  <>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Authorize with Spotify
                  </>
                )}
              </Button>
            </div>
          ) : profile ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Profile Information */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                      Profile Information
                    </h3>
                    <div className="flex items-center space-x-2">
                      {getConnectionStatusIcon(profile.connection_status)}
                        <span className={`text-sm font-medium ${getConnectionStatusColor(profile.connection_status)}`}>
                          {formatConnectionStatus(profile.connection_status)}
                        </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Avatar and Basic Info */}
                  <div className="flex items-center space-x-4">
                    {profile.avatar_url ? (
                      <img
                        src={profile.avatar_url}
                        alt={profile.display_name}
                        className="w-16 h-16 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-16 h-16 bg-slate-200 dark:bg-slate-700 rounded-full flex items-center justify-center">
                        <User className="h-8 w-8 text-slate-400" />
                      </div>
                    )}
                    <div>
                      <h4 className="text-lg font-medium text-slate-900 dark:text-slate-100">
                        {profile.display_name}
                      </h4>
                      <p className="text-sm text-slate-500 dark:text-slate-400">
                        {profile.email || 'No email provided'}
                      </p>
                      <div className="flex items-center space-x-2 mt-1">
                        <Crown className="h-4 w-4 text-yellow-500" />
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                          {profile.subscription_type || 'Free'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                      <div className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {profile.follower_count || 0}
                      </div>
                      <div className="text-sm text-slate-500 dark:text-slate-400">Followers</div>
                    </div>
                    <div className="text-center p-3 bg-slate-50 dark:bg-slate-700 rounded-lg">
                      <div className="flex items-center justify-center space-x-1">
                        <Globe className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                          {profile.country || 'Unknown'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Last Updated */}
                  <div className="flex items-center justify-between text-sm text-slate-500 dark:text-slate-400">
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-4 w-4" />
                      <span>Last updated: {lastUpdated ? new Date(lastUpdated).toLocaleString() : 'Unknown'}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Connection Actions */}
              <Card>
                <CardHeader>
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                    Connection Management
                  </h3>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <Button
                      onClick={handleRefreshConnection}
                      disabled={isRefreshing}
                      className="w-full"
                      variant="secondary"
                    >
                      {isRefreshing ? (
                        <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                      ) : (
                        <RefreshCw className="h-4 w-4 mr-2" />
                      )}
                      Refresh Connection
                    </Button>

                    {profile.connection_status !== 'active' && (
                      <Button
                        onClick={handleReauthorize}
                        className="w-full"
                        variant="primary"
                      >
                        <SiSpotify className="h-4 w-4 mr-2" />
                        Reauthorize Spotify
                      </Button>
                    )}

                    <Button
                      onClick={() => window.open(`https://open.spotify.com/user/${profile.spotify_id}`, '_blank')}
                      variant="ghost"
                      className="w-full"
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Spotify Profile
                    </Button>
                  </div>

                  {/* Connection Info */}
                  <div className="p-4 bg-slate-50 dark:bg-slate-700 rounded-lg">
                    <h4 className="text-sm font-medium text-slate-900 dark:text-slate-100 mb-2">
                      Connection Details
                    </h4>
                    <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1">
                      <div>ID: {profile.spotify_id}</div>
                      {profile.last_activity && (
                        <div>Last Activity: {new Date(profile.last_activity).toLocaleString()}</div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Recently Played Tracks */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <Headphones className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                      <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                        Recently Played Tracks
                      </h3>
                    </div>
                    <span className="text-sm text-slate-500 dark:text-slate-400">
                      {recentlyPlayed.length} tracks
                    </span>
                  </div>
                </CardHeader>
                <CardContent>
                  {recentlyPlayed.length > 0 ? (
                    <div className="space-y-3 max-h-60 overflow-y-auto">
                      {recentlyPlayed.map((track, index) => (
                        <div
                          key={`${track.track_uri}-${index}`}
                          className="flex items-center space-x-3 p-3 bg-slate-50 dark:bg-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-600 transition-colors"
                        >
                          <Music className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-slate-900 dark:text-slate-100 truncate">
                              {track.track_name}
                            </div>
                            <div className="text-sm text-slate-500 dark:text-slate-400 truncate">
                              {track.artist_name} • {track.album_name}
                            </div>
                          </div>
                          <div className="flex items-center space-x-2 flex-shrink-0">
                            <Clock className="h-3 w-3 text-slate-400" />
                            <span className="text-xs text-slate-500 dark:text-slate-400">
                              {formatLastPlayed(track.played_at)}
                            </span>
                            <Button
                              onClick={() => window.open(track.external_url, '_blank')}
                              variant="ghost"
                              className="p-1"
                            >
                              <ExternalLink className="h-3 w-3" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500 dark:text-slate-400">
                      <Music className="h-12 w-12 mx-auto mb-3 text-slate-300 dark:text-slate-600" />
                      <p>No recently played tracks available</p>
                      <p className="text-sm">Make sure you've been listening to music on Spotify</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : (
            <div className="text-center py-12">
              <Shield className="h-12 w-12 text-slate-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 dark:text-slate-100 mb-2">
                No Verification Data
              </h3>
              <p className="text-slate-600 dark:text-slate-400 mb-4">
                Unable to load Spotify verification details for this account.
              </p>
              <Button
                onClick={startOAuthVerification}
                disabled={isStartingOAuth}
                className="bg-green-500 hover:bg-green-600 text-white"
              >
                {isStartingOAuth ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin mr-2" />
                    Starting Verification...
                  </>
                ) : (
                  <>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Verify Spotify Account
                  </>
                )}
              </Button>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}; 