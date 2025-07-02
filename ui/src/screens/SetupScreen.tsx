import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import { VerificationModal } from '../components/ui/VerificationModal';
import { CheckCircle, Shield } from 'lucide-react';
import * as api from '../api/client';

interface SetupScreenProps {
  onSetupComplete: (session: any) => void;
}

interface User {
  user_id: string;
  display_name: string;
  spotify_client_id: string;
  has_credentials: boolean;
  created_at: string;
  last_used?: string;
  spotify_verified?: boolean;
  spotify_profile?: any;
  last_verification?: string;
}

export function SetupScreen({ onSetupComplete }: SetupScreenProps) {
  const [mode, setMode] = useState<'welcome' | 'new-user' | 'existing-user'>('welcome');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [existingUsers, setExistingUsers] = useState<User[]>([]);
  
  // Verification modal state
  const [showVerificationModal, setShowVerificationModal] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  
  // New user form state
  const [formData, setFormData] = useState({
    spotify_client_id: '',
    spotify_client_secret: '',
    display_name: ''
  });

  // Fetch existing users
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const users = await api.listUsers();
        setExistingUsers(users);
      } catch (error) {
        console.warn('Could not fetch existing users:', error);
      }
    };
    fetchUsers();
  }, []);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.spotify_client_id.trim() || !formData.spotify_client_secret.trim()) {
      setError('Please provide both Spotify Client ID and Client Secret');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await api.createUser({
        spotify_client_id: formData.spotify_client_id.trim(),
        spotify_client_secret: formData.spotify_client_secret.trim(),
        display_name: formData.display_name.trim() || undefined
      });

      if (result.success) {
        onSetupComplete(result.session);
      } else {
        setError(result.error || 'Failed to create user account');
      }
    } catch (error) {
      setError('Failed to create user account. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginUser = async (userId: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await api.loginUser(userId);
      if (result.success) {
        onSetupComplete(result.session);
      } else {
        setError(result.error || 'Login failed');
      }
    } catch (error) {
      setError('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleVerificationClick = (userId: string) => {
    setSelectedUserId(userId);
    setShowVerificationModal(true);
  };

  // Welcome Screen
  if (mode === 'welcome') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-fuchsia-600 rounded-2xl flex items-center justify-center">
                <span className="text-2xl font-bold text-white">🎵</span>
              </div>
            </div>
            <h1 className="font-sans text-3xl md:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100 mb-4">
              Anghami to Spotify Migration Tool
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-400 leading-relaxed max-w-xl mx-auto">
              Automatically extract playlists from your Anghami profile and migrate them to Spotify with intelligent track matching.
            </p>
          </div>

          <Card className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-3">
                Setup Spotify Access
              </h2>
              <p className="text-slate-600 dark:text-slate-400">
                We need Spotify API access to create playlists in your account
              </p>
            </div>

            <div className="space-y-4">
              <Button
                onClick={() => setMode('new-user')}
                className="w-full"
                variant="primary"
              >
                Setup Spotify Integration
              </Button>

              {existingUsers.length > 0 && (
                <Button
                  onClick={() => setMode('existing-user')}
                  className="w-full"
                  variant="secondary"
                >
                  Use Existing Setup ({existingUsers.length} available)
                </Button>
              )}
            </div>

            <div className="mt-8 p-4 bg-slate-100 dark:bg-slate-800 rounded-lg">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 mb-2">
                📋 How this works:
              </h3>
              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                <li>• <span className="font-medium text-fuchsia-600">Anghami:</span> We extract playlist data from your public profile (no login required)</li>
                <li>• <span className="font-medium text-emerald-600">Spotify:</span> We create playlists using your Developer App credentials</li>
                <li>• You'll need: Spotify Client ID & Secret from <span className="text-emerald-600 dark:text-emerald-400 font-mono">developer.spotify.com</span></li>
              </ul>
            </div>

            {/* Detailed Setup Guide */}
            <div className="mt-6 p-6 bg-gradient-to-br from-emerald-50 to-fuchsia-50 dark:from-slate-800 dark:to-slate-700 rounded-xl border border-emerald-200 dark:border-slate-600">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-emerald-500 rounded-lg flex items-center justify-center mr-3">
                  <span className="text-white font-bold">📚</span>
                </div>
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                  How to Get Your Spotify Credentials
                </h3>
              </div>

              <div className="space-y-4 text-sm">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Step 1-4 */}
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-emerald-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">1</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Visit Spotify Developer Dashboard</p>
                        <a 
                          href="https://developer.spotify.com/dashboard" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 underline font-mono text-xs"
                        >
                          developer.spotify.com/dashboard
                        </a>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-emerald-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">2</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Login with your Spotify account</p>
                        <p className="text-slate-600 dark:text-slate-400">Use your regular Spotify login credentials</p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-emerald-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">3</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Click "Create App"</p>
                        <a 
                          href="https://developer.spotify.com/dashboard/create" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-emerald-300 underline font-mono text-xs"
                        >
                          developer.spotify.com/dashboard/create
                        </a>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-emerald-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">4</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Fill out the app details</p>
                        <div className="mt-2 p-3 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-600">
                          <div className="space-y-2">
                            <div>
                              <span className="font-medium text-slate-700 dark:text-slate-300">App Name:</span>
                              <div className="font-mono text-xs bg-slate-100 dark:bg-slate-800 p-1 rounded mt-1 text-slate-800 dark:text-slate-200">
                                Anghami to Spotify Migrator
                              </div>
                            </div>
                            <div>
                              <span className="font-medium text-slate-700 dark:text-slate-300">Description:</span>
                              <div className="font-mono text-xs bg-slate-100 dark:bg-slate-800 p-1 rounded mt-1 text-slate-800 dark:text-slate-200">
                                Personal tool for migrating playlists from Anghami to Spotify
                              </div>
                            </div>
                            <div>
                              <span className="font-medium text-slate-700 dark:text-slate-300">Website:</span>
                              <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                                Leave empty
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Step 5-8 */}
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-fuchsia-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">5</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Add Redirect URI</p>
                        <div className="mt-2 p-2 bg-white dark:bg-slate-900 rounded border border-slate-200 dark:border-slate-600">
                          <div className="font-mono text-xs text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 p-1 rounded">
                            http://127.0.0.1:8888/callback
                          </div>
                        </div>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Copy this exactly</p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-fuchsia-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">6</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Select API Type</p>
                        <div className="mt-1 p-2 bg-sky-50 dark:bg-sky-900/20 rounded border border-sky-200 dark:border-sky-800">
                          <p className="text-sky-800 dark:text-sky-200 font-medium">✓ Web API</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-fuchsia-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">7</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Accept Terms & Save</p>
                        <p className="text-slate-600 dark:text-slate-400">✓ Check "I understand and agree with Spotify's Developer Terms of Service"</p>
                        <p className="text-slate-600 dark:text-slate-400">Then click "Save"</p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-fuchsia-500 text-white rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">8</div>
                      <div>
                        <p className="font-medium text-slate-900 dark:text-slate-100">Copy Your Credentials</p>
                        <div className="space-y-2 mt-2">
                          <div className="p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded border border-emerald-200 dark:border-emerald-800">
                            <p className="text-emerald-800 dark:text-emerald-200 font-medium text-xs">1. Copy "Client ID" (visible)</p>
                          </div>
                          <div className="p-2 bg-amber-50 dark:bg-amber-900/20 rounded border border-amber-200 dark:border-amber-800">
                            <p className="text-amber-800 dark:text-amber-200 font-medium text-xs">2. Click "View client secret" & copy it</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-sky-50 dark:bg-sky-900/20 rounded-lg border border-sky-200 dark:border-sky-800">
                  <div className="flex items-start space-x-2">
                    <span className="text-sky-600 dark:text-sky-400 text-lg">💡</span>
                    <div>
                      <p className="font-medium text-sky-900 dark:text-sky-100">Pro Tip</p>
                      <p className="text-sky-700 dark:text-sky-300 text-xs">
                        Your credentials are unique to your Spotify account and allow this tool to create playlists on your behalf. 
                        They're stored securely and only used for migration purposes.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  // New User Registration
  if (mode === 'new-user') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-lg">
          <Card className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-3">
                Create Your Account
              </h2>
              <p className="text-slate-600 dark:text-slate-400">
                Enter your Spotify app credentials to get started
              </p>
            </div>

            <form onSubmit={handleCreateUser} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Display Name (Optional)
                </label>
                <Input
                  type="text"
                  value={formData.display_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, display_name: e.target.value }))}
                  placeholder="Your name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Spotify Client ID <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="text"
                  value={formData.spotify_client_id}
                  onChange={(e) => setFormData(prev => ({ ...prev, spotify_client_id: e.target.value }))}
                  placeholder="32-character Client ID"
                  className="font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Spotify Client Secret <span className="text-rose-500">*</span>
                </label>
                <Input
                  type="password"
                  value={formData.spotify_client_secret}
                  onChange={(e) => setFormData(prev => ({ ...prev, spotify_client_secret: e.target.value }))}
                  placeholder="32-character Client Secret"
                  className="font-mono text-sm"
                />
              </div>

              {error && (
                <div className="p-3 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-md">
                  <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  type="button"
                  onClick={() => setMode('welcome')}
                  variant="secondary"
                  className="flex-1"
                  disabled={loading}
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Account'}
                </Button>
              </div>
            </form>

            <div className="mt-6 p-4 bg-sky-50 dark:bg-sky-900/20 border border-sky-200 dark:border-sky-800 rounded-lg">
              <h4 className="font-medium text-sky-900 dark:text-sky-100 mb-2">
                🔒 Security Note
              </h4>
              <p className="text-xs text-sky-700 dark:text-sky-300">
                Your credentials are encrypted and stored securely. They're only used for Spotify API authentication.
              </p>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  // Existing User Login
  if (mode === 'existing-user') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex items-center justify-center p-4">
        <div className="w-full max-w-2xl">
          <Card className="p-8">
            <div className="text-center mb-8">
              <h2 className="text-xl md:text-2xl font-semibold text-slate-900 dark:text-slate-100 mb-3">
                Welcome Back
              </h2>
              <p className="text-slate-600 dark:text-slate-400">
                Select your account to continue
              </p>
            </div>

            {error && (
              <div className="mb-6 p-3 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-md">
                <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>
              </div>
            )}

            <div className="space-y-3 mb-6">
              {existingUsers.map((user) => (
                <div
                  key={user.user_id}
                  className="flex items-center justify-between p-4 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-slate-900 dark:text-slate-100">
                        {user.display_name}
                      </h3>
                      {/* Verification Badge */}
                      {user.spotify_verified ? (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleVerificationClick(user.user_id);
                          }}
                          className="flex items-center space-x-1 hover:opacity-80 transition-opacity"
                          title="Click to view verification details"
                        >
                          <CheckCircle className="h-4 w-4 text-blue-500" />
                          <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                            Verified
                          </span>
                        </button>
                      ) : (
                        <div className="flex items-center space-x-1">
                          <Shield className="h-3 w-3 text-amber-500" />
                          <span className="text-xs text-amber-600 dark:text-amber-400">
                            Not Verified
                          </span>
                        </div>
                      )}
                    </div>
                    <div className="text-sm text-slate-500 dark:text-slate-400 space-y-1">
                      <p>Client ID: <span className="font-mono">{user.spotify_client_id.slice(0, 8)}...{user.spotify_client_id.slice(-4)}</span></p>
                      <p>
                        {user.last_used ? `Last used: ${formatDate(user.last_used)}` : `Created: ${formatDate(user.created_at)}`}
                      </p>
                      {user.spotify_verified && user.last_verification && (
                        <p className="text-xs text-emerald-600 dark:text-emerald-400">
                          Verified: {formatDate(user.last_verification)}
                        </p>
                      )}
                    </div>
                  </div>
                  <Button
                    onClick={() => handleLoginUser(user.user_id)}
                    variant="primary"
                    disabled={loading}
                  >
                    {loading ? 'Logging in...' : 'Login'}
                  </Button>
                </div>
              ))}
            </div>

            <div className="flex gap-3">
              <Button
                onClick={() => setMode('welcome')}
                variant="secondary"
                className="flex-1"
                disabled={loading}
              >
                Back
              </Button>
              <Button
                onClick={() => setMode('new-user')}
                variant="ghost"
                className="flex-1"
                disabled={loading}
              >
                Create New Account
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Verification Modal */}
      {selectedUserId && (
        <VerificationModal
          isOpen={showVerificationModal}
          onClose={() => {
            setShowVerificationModal(false);
            setSelectedUserId(null);
          }}
          userId={selectedUserId}
          onProfileUpdate={() => {
            // Optionally refresh users list to update verification status
            // We could call fetchUsers() here if needed
          }}
        />
      )}
    </>
  );
} 