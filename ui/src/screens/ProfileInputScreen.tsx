import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Music, CheckCircle, AlertCircle, ExternalLink, User, Clock, Hash, ChevronDown } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { ProgressBar } from '../components/ui/Progress';
import { toast } from 'react-hot-toast';
import { SiSpotify } from 'react-icons/si';

// API types
interface ProfileData {
  profile_url: string;
  display_name?: string;
  avatar_url?: string;
  follower_count?: number;
  is_valid: boolean;
  error_message?: string;
}

interface ProfileHistoryItem {
  id: number;
  profile_url: string;
  display_name?: string;
  avatar_url?: string;
  follower_count?: number;
  usage_count: number;
  last_used: string;
}

interface ProfileInputScreenProps {
  onProfileConfirmed: (profile: ProfileData) => void;
  onBack?: () => void;
}

type ValidationState = 'idle' | 'validating' | 'valid' | 'invalid';

export const ProfileInputScreen: React.FC<ProfileInputScreenProps> = ({ 
  onProfileConfirmed,
  onBack 
}) => {
  const [profileUrl, setProfileUrl] = useState('');
  const [validationState, setValidationState] = useState<ValidationState>('idle');
  const [profileData, setProfileData] = useState<ProfileData | null>(null);
  const [profileHistory, setProfileHistory] = useState<ProfileHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Load profile history on component mount
  useEffect(() => {
    loadProfileHistory();
  }, []);

  const loadProfileHistory = async () => {
    try {
      const response = await fetch('http://localhost:8000/profiles/history');
      if (response.ok) {
        const history = await response.json();
        setProfileHistory(history);
      }
    } catch (error) {
      console.error('Failed to load profile history:', error);
    }
  };

  const validateProfileUrl = (url: string): boolean => {
    const anghamiProfilePattern = /^https?:\/\/(play\.anghami\.com|anghami\.com|www\.anghami\.com)\/profile\/[\w-]+/;
    return anghamiProfilePattern.test(url);
  };

  const handleProfileValidation = async (url: string) => {
    if (!url.trim()) {
      setValidationState('idle');
      setProfileData(null);
      return;
    }

    if (!validateProfileUrl(url)) {
      setValidationState('invalid');
      setProfileData({
        profile_url: url,
        is_valid: false,
        error_message: 'Please enter a valid Anghami profile URL (e.g., https://play.anghami.com/profile/username)'
      });
      return;
    }

    setValidationState('validating');
    
    try {
      const response = await fetch('http://localhost:8000/profiles/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ profile_url: url }),
      });

      if (response.ok) {
        const data: ProfileData = await response.json();
        setProfileData(data);
        setValidationState(data.is_valid ? 'valid' : 'invalid');
        
        if (data.is_valid) {
          toast.success('Profile found successfully!');
          // Reload history since a new profile was added
          loadProfileHistory();
        } else {
          toast.error(data.error_message || 'Failed to validate profile');
        }
      } else {
        throw new Error('Profile validation failed');
      }
    } catch (error) {
      console.error('Profile validation error:', error);
      setValidationState('invalid');
      setProfileData({
        profile_url: url,
        is_valid: false,
        error_message: 'Unable to validate profile. Please check your connection and try again.'
      });
      toast.error('Profile validation failed');
    }
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const url = e.target.value;
    setProfileUrl(url);
    
    // Debounce validation
    const timeoutId = setTimeout(() => {
      handleProfileValidation(url);
    }, 500);

    return () => clearTimeout(timeoutId);
  };

  const handleHistoryItemSelect = (item: ProfileHistoryItem) => {
    setProfileUrl(item.profile_url);
    setShowHistory(false);
    handleProfileValidation(item.profile_url);
  };

  const handleConfirmProfile = async () => {
    if (!profileData || !profileData.is_valid) return;

    setIsLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/profiles/confirm', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ profile_url: profileData.profile_url }),
      });

      if (response.ok) {
        const confirmedData: ProfileData = await response.json();
        toast.success(`Welcome, ${confirmedData.display_name || 'Anghami User'}!`);
        onProfileConfirmed(confirmedData);
      } else {
        throw new Error('Profile confirmation failed');
      }
    } catch (error) {
      console.error('Profile confirmation error:', error);
      toast.error('Failed to confirm profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const getValidationIcon = () => {
    switch (validationState) {
      case 'validating':
        return <div className="h-5 w-5 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />;
      case 'valid':
        return <CheckCircle className="h-5 w-5 text-emerald-500" />;
      case 'invalid':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };

  const formatLastUsed = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4 sm:p-6 lg:p-8">
      <div className="w-full max-w-2xl">
        {/* Header with Back Button - Following design guidelines */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          {/* Clean Back Navigation */}
          {onBack && (
            <div className="flex justify-start mb-6">
              <button
                onClick={onBack}
                className="inline-flex items-center px-3 py-2 rounded-md bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 transition-all duration-300 ease-in-out focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back to Setup
              </button>
            </div>
          )}

          <div className="text-center">
            {/* Clean Logo Design following guidelines */}
            <div className="flex items-center justify-center mb-6">
              <div className="flex items-center space-x-2">
                <div className="w-12 h-12 bg-fuchsia-600 rounded-md flex items-center justify-center">
                  <Music className="h-7 w-7 text-white" />
                </div>
                <svg className="w-6 h-6 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <div className="w-12 h-12 bg-emerald-600 rounded-md flex items-center justify-center">
                  <SiSpotify className="h-7 w-7 text-white" />
                </div>
              </div>
            </div>
            
            {/* Typography following design guidelines - Display/h1 */}
            <h1 className="font-sans text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mb-4">
              Enter Your Anghami Profile
            </h1>
            {/* Body text */}
            <p className="text-base leading-relaxed text-slate-600 dark:text-slate-400 max-w-lg mx-auto">
              Provide your Anghami profile URL to discover and migrate your playlists
            </p>
          </div>
        </motion.div>

        {/* Progress */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          className="mb-8"
        >
          <ProgressBar
            value={profileData?.is_valid ? 50 : 25}
            showLabel
            label="Profile Setup Progress"
            className="mb-2"
          />
          <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
            {profileData?.is_valid ? 'Profile validated successfully' : 'Enter your profile URL to continue'}
          </p>
        </motion.div>

        {/* Main Content - Following Card design guidelines */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="mb-6">
            <CardHeader>
              {/* Section heading following guidelines */}
              <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
                Anghami Profile URL
              </h2>
              <p className="text-base leading-relaxed text-slate-600 dark:text-slate-400">
                Enter your Anghami profile URL to begin the migration process
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Profile URL Input - Following form input guidelines */}
              <div className="relative">
                <Input
                  type="url"
                  placeholder="https://play.anghami.com/profile/your-username"
                  value={profileUrl}
                  onChange={handleUrlChange}
                  className={`w-full rounded-md border bg-white dark:bg-slate-800 px-3 py-2 text-sm focus:outline-none focus:ring-2 transition-all duration-300 ease-in-out ${
                    validationState === 'valid' ? 'border-emerald-500 focus:ring-emerald-500' :
                    validationState === 'invalid' ? 'border-rose-600 focus:ring-rose-500' : 
                    'border-slate-300 dark:border-slate-600 focus:ring-emerald-500'
                  }`}
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  {getValidationIcon()}
                </div>
              </div>

              {/* Validation Message */}
              {profileData && !profileData.is_valid && (
                <div className="flex items-start space-x-2 text-xs text-rose-600 dark:text-rose-400">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{profileData.error_message}</span>
                </div>
              )}

              {/* Profile History Dropdown */}
              {profileHistory.length > 0 && (
                <div className="relative">
                  <Button
                    variant="secondary"
                    onClick={() => setShowHistory(!showHistory)}
                    className="w-full justify-between"
                  >
                    <span className="flex items-center space-x-2">
                      <Clock className="h-4 w-4" />
                      <span>Recent Profiles ({profileHistory.length})</span>
                    </span>
                    <ChevronDown className={`h-4 w-4 transition-all duration-300 ease-in-out ${showHistory ? 'rotate-180' : ''}`} />
                  </Button>

                  {showHistory && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-sm z-10 max-h-64 overflow-y-auto"
                    >
                      {profileHistory.map((item) => (
                        <button
                          key={item.id}
                          onClick={() => handleHistoryItemSelect(item)}
                          className="w-full px-4 py-3 text-left hover:bg-slate-50 dark:hover:bg-slate-700 border-b border-slate-100 dark:border-slate-600 last:border-b-0 transition-all duration-300 ease-in-out"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-3 flex-1 min-w-0">
                              {/* Profile Avatar in History */}
                              <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden">
                                {item.avatar_url ? (
                                  <img
                                    src={item.avatar_url}
                                    alt={`${item.display_name || 'User'}'s avatar`}
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
                              <div className="flex-1 min-w-0">
                                <div className="font-medium text-slate-900 dark:text-slate-100 truncate text-sm">
                                  {item.display_name || 'Anghami User'}
                                </div>
                                <div className="text-xs text-slate-500 dark:text-slate-400 truncate">
                                  {item.profile_url}
                                </div>
                              </div>
                            </div>
                            <div className="text-right text-xs text-slate-500 dark:text-slate-400 ml-2">
                              <div className="flex items-center space-x-1">
                                <Hash className="h-3 w-3" />
                                <span>{item.usage_count}</span>
                              </div>
                              <div>{formatLastUsed(item.last_used)}</div>
                            </div>
                          </div>
                        </button>
                      ))}
                    </motion.div>
                  )}
                </div>
              )}

              {/* Profile Preview */}
              {profileData && profileData.is_valid && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-emerald-50 dark:bg-emerald-900/20 rounded-lg p-4 border border-emerald-200 dark:border-emerald-800"
                >
                  <div className="flex items-center space-x-4">
                    {/* Profile Avatar - Now displays actual image */}
                    <div className="w-12 h-12 rounded-full flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {profileData.avatar_url ? (
                        <img
                          src={profileData.avatar_url}
                          alt={`${profileData.display_name || 'User'}'s avatar`}
                          className="w-full h-full object-cover rounded-full"
                          onError={(e) => {
                            // Fallback to icon if image fails to load
                            const target = e.target as HTMLImageElement;
                            target.style.display = 'none';
                            const parent = target.parentElement;
                            if (parent) {
                              parent.classList.add('bg-emerald-600');
                              parent.innerHTML = '<svg class="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>';
                            }
                          }}
                        />
                      ) : (
                        <div className="w-full h-full bg-emerald-600 rounded-full flex items-center justify-center">
                          <User className="h-6 w-6 text-white" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-slate-900 dark:text-slate-100">
                        {profileData.display_name || 'Anghami User'}
                      </h3>
                      <p className="text-sm text-slate-600 dark:text-slate-400 truncate">
                        {profileData.profile_url}
                      </p>
                      {profileData.follower_count !== undefined && (
                        <p className="text-xs text-emerald-700 dark:text-emerald-300">
                          {profileData.follower_count} followers
                        </p>
                      )}
                    </div>
                    <CheckCircle className="h-6 w-6 text-emerald-600 flex-shrink-0" />
                  </div>
                </motion.div>
              )}

              {/* Example URL - Clean design */}
              <div className="bg-slate-50 dark:bg-slate-800 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <ExternalLink className="h-5 w-5 text-slate-500 dark:text-slate-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-slate-900 dark:text-slate-100 mb-2">
                      How to find your profile URL:
                    </h4>
                    <ol className="text-sm text-slate-600 dark:text-slate-400 space-y-1 leading-relaxed">
                      <li>1. Open Anghami and go to your profile</li>
                      <li>2. Copy the URL from your browser's address bar</li>
                      <li>3. It should look like: <code className="font-mono text-sm bg-slate-200 dark:bg-slate-700 px-1 rounded">https://play.anghami.com/profile/username</code></li>
                    </ol>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Continue Button - Following button guidelines */}
          {profileData && profileData.is_valid && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <Button
                variant="primary"
                size="lg"
                onClick={handleConfirmProfile}
                disabled={isLoading}
                loading={isLoading}
                className="w-full sm:w-auto"
              >
                Continue with This Profile
              </Button>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}; 