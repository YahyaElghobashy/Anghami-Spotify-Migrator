import React, { useState, useEffect } from 'react';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card } from '../components/ui/Card';
import * as api from '../api/client';
import { User, Edit3, Trash2, Plus, Settings, Shield, Clock } from 'lucide-react';

interface UserProfileScreenProps {
  currentSession: any;
  onProfileSwitch: (session: any) => void;
  onBackToApp: () => void;
  onLogout: () => void;
}

interface User {
  user_id: string;
  display_name: string;
  spotify_client_id: string;
  has_credentials: boolean;
  created_at: string;
  last_used?: string;
}

export function UserProfileScreen({ currentSession, onProfileSwitch, onBackToApp, onLogout }: UserProfileScreenProps) {
  const [mode, setMode] = useState<'view' | 'edit' | 'manage'>('view');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  
  // Edit form state
  const [editForm, setEditForm] = useState({
    display_name: currentSession?.display_name || '',
    spotify_client_id: currentSession?.spotify_client_id || '',
    spotify_client_secret: ''
  });

  // Load all users for profile switching
  useEffect(() => {
    const loadUsers = async () => {
      try {
        const users = await api.listUsers();
        setAllUsers(users);
      } catch (error) {
        console.warn('Could not load users:', error);
      }
    };
    loadUsers();
  }, []);

  const handleSwitchProfile = async (userId: string) => {
    setLoading(true);
    setError(null);

    try {
      const result = await api.loginUser(userId);
      if (result.success) {
        onProfileSwitch(result.session);
      } else {
        setError(result.error || 'Failed to switch profile');
      }
    } catch (error) {
      setError('Failed to switch profile');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // For now, we'll show a success message since profile update isn't implemented yet
      // In a full implementation, you'd have an API endpoint to update user info
      console.log('Profile update would be implemented here', editForm);
      setMode('view');
      setError(null);
    } catch (error) {
      setError('Failed to update profile');
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

  const otherUsers = allUsers.filter(user => user.user_id !== currentSession?.user_id);

  // Profile View Mode
  if (mode === 'view') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center space-x-4">
              <Button
                onClick={onBackToApp}
                variant="ghost"
                className="flex items-center space-x-2"
              >
                <span>← Back to App</span>
              </Button>
            </div>
            <div className="flex items-center space-x-3">
              <Button
                onClick={() => setMode('manage')}
                variant="secondary"
                className="flex items-center space-x-2"
              >
                <Settings className="h-4 w-4" />
                <span>Manage Profiles</span>
              </Button>
              <Button
                onClick={onLogout}
                variant="ghost"
                className="text-red-600 hover:text-red-700"
              >
                Logout
              </Button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Profile Card */}
            <div className="lg:col-span-2">
              <Card className="p-8">
                <div className="flex items-start justify-between mb-6">
                  <div className="flex items-center space-x-4">
                    <div className="w-16 h-16 bg-gradient-to-br from-emerald-500 to-fuchsia-600 rounded-2xl flex items-center justify-center">
                      <User className="h-8 w-8 text-white" />
                    </div>
                    <div>
                      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                        {currentSession?.display_name}
                      </h1>
                      <p className="text-slate-600 dark:text-slate-400">
                        Spotify Account Linked
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={() => setMode('edit')}
                    variant="ghost"
                    className="flex items-center space-x-2"
                  >
                    <Edit3 className="h-4 w-4" />
                    <span>Edit</span>
                  </Button>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Display Name
                    </label>
                    <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                      {currentSession?.display_name}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Spotify Client ID
                    </label>
                    <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg font-mono text-sm">
                      {currentSession?.spotify_client_id}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                      Account Created
                    </label>
                    <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                      {formatDate(currentSession?.created_at)}
                    </div>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Shield className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
                    <div>
                      <p className="font-medium text-emerald-900 dark:text-emerald-100">
                        Secure Account
                      </p>
                      <p className="text-sm text-emerald-700 dark:text-emerald-300">
                        Your Spotify credentials are encrypted and stored securely
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Quick Actions Sidebar */}
            <div className="space-y-6">
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
                  Quick Actions
                </h3>
                <div className="space-y-3">
                  <Button
                    onClick={onBackToApp}
                    variant="primary"
                    className="w-full justify-start"
                  >
                    Continue Migration
                  </Button>
                  <Button
                    onClick={() => setMode('manage')}
                    variant="secondary"
                    className="w-full justify-start"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add Another Profile
                  </Button>
                  <Button
                    onClick={() => setMode('edit')}
                    variant="ghost"
                    className="w-full justify-start"
                  >
                    <Edit3 className="h-4 w-4 mr-2" />
                    Edit Profile
                  </Button>
                </div>
              </Card>

              {/* Other Profiles */}
              {otherUsers.length > 0 && (
                <Card className="p-6">
                  <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
                    Switch Profile
                  </h3>
                  <div className="space-y-3">
                    {otherUsers.map((user) => (
                      <div
                        key={user.user_id}
                        className="flex items-center justify-between p-3 border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 bg-gradient-to-br from-fuchsia-500 to-emerald-500 rounded-lg flex items-center justify-center">
                            <User className="h-4 w-4 text-white" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900 dark:text-slate-100 text-sm">
                              {user.display_name}
                            </p>
                            {user.last_used && (
                              <p className="text-xs text-slate-500 dark:text-slate-400">
                                <Clock className="h-3 w-3 inline mr-1" />
                                {formatDate(user.last_used)}
                              </p>
                            )}
                          </div>
                        </div>
                        <Button
                          onClick={() => handleSwitchProfile(user.user_id)}
                          variant="ghost"
                          size="sm"
                          disabled={loading}
                        >
                          Switch
                        </Button>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Edit Mode
  if (mode === 'edit') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-4">
        <div className="max-w-2xl mx-auto">
          <Card className="p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Edit Profile
              </h2>
              <Button
                onClick={() => setMode('view')}
                variant="ghost"
              >
                Cancel
              </Button>
            </div>

            <form onSubmit={handleUpdateProfile} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Display Name
                </label>
                <Input
                  type="text"
                  value={editForm.display_name}
                  onChange={(e) => setEditForm(prev => ({ ...prev, display_name: e.target.value }))}
                  placeholder="Your display name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  Spotify Client ID
                </label>
                <Input
                  type="text"
                  value={editForm.spotify_client_id}
                  onChange={(e) => setEditForm(prev => ({ ...prev, spotify_client_id: e.target.value }))}
                  placeholder="32-character Client ID"
                  className="font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                  New Spotify Client Secret (optional)
                </label>
                <Input
                  type="password"
                  value={editForm.spotify_client_secret}
                  onChange={(e) => setEditForm(prev => ({ ...prev, spotify_client_secret: e.target.value }))}
                  placeholder="Leave empty to keep current secret"
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                  Only enter if you want to update your secret
                </p>
              </div>

              {error && (
                <div className="p-3 bg-rose-50 dark:bg-rose-900/20 border border-rose-200 dark:border-rose-800 rounded-md">
                  <p className="text-sm text-rose-600 dark:text-rose-400">{error}</p>
                </div>
              )}

              <div className="flex gap-3">
                <Button
                  type="button"
                  onClick={() => setMode('view')}
                  variant="secondary"
                  className="flex-1"
                  disabled={loading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    );
  }

  // Manage Profiles Mode
  if (mode === 'manage') {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
              Manage Profiles
            </h1>
            <Button
              onClick={() => setMode('view')}
              variant="secondary"
            >
              Back to Profile
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Current Profile */}
            <Card className="p-6 border-emerald-200 dark:border-emerald-800">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-emerald-900 dark:text-emerald-100">
                  Current Profile
                </h3>
                <span className="px-2 py-1 bg-emerald-100 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-200 text-xs rounded-full">
                  Active
                </span>
              </div>
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-12 h-12 bg-gradient-to-br from-emerald-500 to-fuchsia-600 rounded-xl flex items-center justify-center">
                  <User className="h-6 w-6 text-white" />
                </div>
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-100">
                    {currentSession?.display_name}
                  </p>
                  <p className="text-sm text-slate-500 dark:text-slate-400 font-mono">
                    {currentSession?.spotify_client_id?.slice(0, 8)}...
                  </p>
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => setMode('edit')}
                  variant="ghost"
                  size="sm"
                  className="flex-1"
                >
                  <Edit3 className="h-4 w-4 mr-1" />
                  Edit
                </Button>
              </div>
            </Card>

            {/* All Other Profiles */}
            {otherUsers.map((user) => (
              <Card key={user.user_id} className="p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-fuchsia-500 to-emerald-500 rounded-xl flex items-center justify-center">
                    <User className="h-6 w-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-slate-900 dark:text-slate-100">
                      {user.display_name}
                    </p>
                    <p className="text-sm text-slate-500 dark:text-slate-400 font-mono">
                      {user.spotify_client_id.slice(0, 8)}...
                    </p>
                    {user.last_used && (
                      <p className="text-xs text-slate-400 dark:text-slate-500">
                        Last used: {formatDate(user.last_used)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    onClick={() => handleSwitchProfile(user.user_id)}
                    variant="primary"
                    size="sm"
                    className="flex-1"
                    disabled={loading}
                  >
                    Switch
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))}

            {/* Add New Profile */}
            <Card className="p-6 border-dashed border-2 border-slate-300 dark:border-slate-600">
              <div className="text-center">
                <div className="w-12 h-12 bg-slate-200 dark:bg-slate-700 rounded-xl flex items-center justify-center mx-auto mb-4">
                  <Plus className="h-6 w-6 text-slate-500 dark:text-slate-400" />
                </div>
                <h3 className="font-medium text-slate-900 dark:text-slate-100 mb-2">
                  Add New Profile
                </h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Create another account for family member or friend
                </p>
                <Button
                  onClick={() => window.location.reload()} // Simple way to go to setup
                  variant="secondary"
                  size="sm"
                >
                  Create Profile
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return null;
} 