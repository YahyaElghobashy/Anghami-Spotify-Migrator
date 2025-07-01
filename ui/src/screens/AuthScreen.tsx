import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { SiSpotify } from 'react-icons/si';
import { Music, CheckCircle, AlertCircle, ExternalLink } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { ProgressBar } from '../components/ui/Progress';

interface AuthScreenProps {
  onAuthComplete: () => void;
}

type AuthStep = 'initial' | 'spotify-auth' | 'anghami-setup' | 'complete';

export const AuthScreen: React.FC<AuthScreenProps> = ({ onAuthComplete }) => {
  const [currentStep, setCurrentStep] = useState<AuthStep>('initial');
  const [isLoading, setIsLoading] = useState(false);
  const [spotifyConnected, setSpotifyConnected] = useState(false);
  const [anghamiSetupComplete, setAnghamiSetupComplete] = useState(false);

  const handleSpotifyAuth = async () => {
    setIsLoading(true);
    setCurrentStep('spotify-auth');
    
    // Simulate OAuth flow
    setTimeout(() => {
      setSpotifyConnected(true);
      setIsLoading(false);
      setCurrentStep('anghami-setup');
    }, 2000);
  };

  const handleAnghamiSetup = async () => {
    setIsLoading(true);
    
    // Simulate setup process
    setTimeout(() => {
      setAnghamiSetupComplete(true);
      setIsLoading(false);
      setCurrentStep('complete');
    }, 1500);
  };

  const handleComplete = () => {
    onAuthComplete();
  };

  const getStepProgress = () => {
    switch (currentStep) {
      case 'initial': return 0;
      case 'spotify-auth': return 25;
      case 'anghami-setup': return 75;
      case 'complete': return 100;
      default: return 0;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <div className="flex items-center justify-center mb-4">
            <div className="p-4 bg-gradient-to-r from-anghami-600 to-spotify-600 rounded-2xl">
              <Music className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-display-sm md:text-display font-extrabold text-slate-900 dark:text-slate-100 mb-2">
            Connect Your Accounts
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400 leading-relaxed">
            Securely link your Spotify account to start migrating your Anghami playlists
          </p>
        </motion.div>

        {/* Progress */}
        <motion.div
          initial={{ opacity: 0, scaleX: 0 }}
          animate={{ opacity: 1, scaleX: 1 }}
          className="mb-8"
        >
          <ProgressBar
            value={getStepProgress()}
            showLabel
            label="Authentication Progress"
            className="mb-6"
          />
        </motion.div>

        {/* Main Content */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="mb-6">
            <CardHeader>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-slate-100">
                Authentication Steps
              </h2>
              <p className="text-slate-600 dark:text-slate-400">
                Follow these steps to connect your accounts securely
              </p>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Spotify Authentication */}
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  {spotifyConnected ? (
                    <CheckCircle className="h-6 w-6 text-spotify-500" />
                  ) : currentStep === 'spotify-auth' ? (
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-spotify-500 border-t-transparent" />
                  ) : (
                    <div className="h-6 w-6 rounded-full border-2 border-slate-300 dark:border-slate-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <SiSpotify className="h-5 w-5 text-spotify-600" />
                    <h3 className="text-base font-medium text-slate-900 dark:text-slate-100">
                      Connect Spotify
                    </h3>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                    Authorize access to create playlists and add tracks to your Spotify account
                  </p>
                  {!spotifyConnected && currentStep === 'initial' && (
                    <Button
                      variant="primary"
                      onClick={handleSpotifyAuth}
                      disabled={isLoading}
                      loading={isLoading}
                      className="flex items-center space-x-2"
                    >
                      <SiSpotify className="h-4 w-4" />
                      <span>Connect with Spotify</span>
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  )}
                  {spotifyConnected && (
                    <div className="flex items-center space-x-2 text-sm text-spotify-600 dark:text-spotify-400">
                      <CheckCircle className="h-4 w-4" />
                      <span>Successfully connected to Spotify</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Anghami Setup */}
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0">
                  {anghamiSetupComplete ? (
                    <CheckCircle className="h-6 w-6 text-spotify-500" />
                  ) : currentStep === 'anghami-setup' ? (
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-anghami-600 border-t-transparent" />
                  ) : (
                    <div className="h-6 w-6 rounded-full border-2 border-slate-300 dark:border-slate-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <div className="w-5 h-5 bg-anghami-600 rounded-sm flex items-center justify-center">
                      <span className="text-white text-xs font-bold">A</span>
                    </div>
                    <h3 className="text-base font-medium text-slate-900 dark:text-slate-100">
                      Setup Anghami Access
                    </h3>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                    Configure access to your Anghami playlists for extraction
                  </p>
                  {spotifyConnected && !anghamiSetupComplete && currentStep === 'anghami-setup' && (
                    <Button
                      variant="secondary"
                      onClick={handleAnghamiSetup}
                      disabled={isLoading}
                      loading={isLoading}
                      className="flex items-center space-x-2"
                    >
                      <Music className="h-4 w-4" />
                      <span>Setup Anghami Access</span>
                    </Button>
                  )}
                  {anghamiSetupComplete && (
                    <div className="flex items-center space-x-2 text-sm text-spotify-600 dark:text-spotify-400">
                      <CheckCircle className="h-4 w-4" />
                      <span>Anghami access configured</span>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Security Note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mb-6"
          >
            <Card className="border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-950">
              <CardContent className="pt-6">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                      Privacy & Security
                    </h4>
                    <p className="text-sm text-blue-800 dark:text-blue-300">
                      We only request the minimum permissions needed to create playlists. 
                      Your credentials are never stored and all authentication is handled 
                      securely through official OAuth2 flows.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Continue Button */}
          {currentStep === 'complete' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center"
            >
              <Button
                variant="primary"
                size="lg"
                onClick={handleComplete}
                className="w-full sm:w-auto"
              >
                Continue to Playlist Selection
              </Button>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
}; 