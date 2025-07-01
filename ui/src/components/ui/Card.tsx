import React, { useState } from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { Music, Clock, PlayCircle, ExternalLink, Users, Eye, EyeOff, ChevronDown, ChevronUp } from 'lucide-react';
import type { EnhancedPlaylist } from '../../api/client';
import { 
  formatPlaylistDuration, 
  getPlaylistTypeLabel, 
  getPlaylistSourceLabel, 
  getPlaylistTypeColor, 
  getPlaylistSourceColor 
} from '../../api/client';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  clickable?: boolean;
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({ 
  className, 
  children, 
  clickable = false, 
  hover = true,
  ...props 
}) => {
  const baseClasses = clsx(
    // Following design guidelines exactly
    'rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm',
    {
      // Hover effects as specified in guidelines
      'hover:shadow-md transition-shadow duration-300': hover,
      'hover:translate-y-[1px] shadow-lift': hover && clickable,
      
      // Clickable states
      'cursor-pointer transition-all duration-300 ease-in-out': clickable,
      'focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2': clickable,
      'active:scale-95': clickable,
    },
    className
  );

  if (clickable) {
    return (
      <motion.div
        whileHover={{ y: 1 }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 400, damping: 17 }}
      >
        <div className={baseClasses} {...props}>
          {children}
        </div>
      </motion.div>
    );
  }

  return (
    <div className={baseClasses} {...props}>
      {children}
    </div>
  );
};

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardHeader: React.FC<CardHeaderProps> = ({ 
  className, 
  children, 
  ...props 
}) => {
  return (
    <div 
      className={clsx('p-6 pb-4', className)} 
      {...props}
    >
      {children}
    </div>
  );
};

export interface CardContentProps extends React.HTMLAttributes<HTMLDivElement> {}

export const CardContent: React.FC<CardContentProps> = ({ 
  className, 
  children, 
  ...props 
}) => {
  return (
    <div className={clsx('px-6 pb-6', className)} {...props}>
      {children}
    </div>
  );
};

Card.displayName = 'Card';
CardHeader.displayName = 'CardHeader';
CardContent.displayName = 'CardContent';

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(
  ({ children, className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={clsx(
          'px-6 py-4 bg-slate-50 dark:bg-slate-800/50',
          'border-t border-slate-200 dark:border-slate-700',
          'rounded-b-lg',
          className
        )}
        {...props}
      >
        {children}
      </div>
    );
  }
);

CardFooter.displayName = 'CardFooter';

interface EnhancedPlaylistCardProps {
  playlist: EnhancedPlaylist;
  isSelected?: boolean;
  onClick?: () => void;
  onToggleSelect?: () => void;
  showPreview?: boolean;
  className?: string;
}

export const EnhancedPlaylistCard: React.FC<EnhancedPlaylistCardProps> = ({
  playlist,
  isSelected = false,
  onClick,
  onToggleSelect,
  showPreview = false,
  className = ''
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const [imageError, setImageError] = useState(false);

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger card click if clicking on interactive elements
    if ((e.target as HTMLElement).closest('button') || (e.target as HTMLElement).closest('input')) {
      return;
    }
    onClick?.();
  };

  const handleToggleDetails = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDetails(!showDetails);
  };

  return (
    <Card
      clickable={!!onClick}
      className={`
        group relative transition-all duration-300 ease-in-out
        ${isSelected ? 'ring-2 ring-emerald-500 shadow-lg' : 'hover:shadow-md'}
        ${className}
      `}
      onClick={handleCardClick}
    >
      <CardContent className="pt-6">
        <div className="flex items-start space-x-4">
          {/* Cover Art */}
          <div className="w-16 h-16 flex-shrink-0 relative">
            {playlist.cover_art_url && !imageError ? (
              <img
                src={playlist.cover_art_url}
                alt={`${playlist.name} cover`}
                className="w-full h-full object-cover rounded-lg"
                onError={() => setImageError(true)}
              />
            ) : (
              <div className={`
                w-full h-full rounded-lg flex items-center justify-center
                ${playlist.source === 'spotify' 
                  ? 'bg-gradient-to-br from-emerald-500 to-emerald-600' 
                  : 'bg-gradient-to-br from-rose-500 to-fuchsia-600'
                }
              `}>
                <Music className="h-8 w-8 text-white" />
              </div>
            )}
            
            {/* Source indicator */}
            <div className={`
              absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs
              ${playlist.source === 'spotify' 
                ? 'bg-emerald-500 text-white' 
                : 'bg-rose-500 text-white'
              }
            `}>
              {playlist.source_indicator}
            </div>
          </div>

          {/* Playlist Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-slate-900 dark:text-slate-100 truncate group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                  {playlist.name}
                </h3>
                
                {/* Creator/Owner */}
                <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                  by {playlist.creator_name || playlist.owner_name || 'Unknown'}
                </p>

                {/* Type and Source badges */}
                <div className="flex items-center space-x-2 mt-2">
                  <span className={`
                    inline-flex items-center px-2 py-1 rounded-md text-xs font-medium
                    ${getPlaylistTypeColor(playlist.type)} bg-opacity-10
                    ${playlist.type === 'owned' || playlist.type === 'created' 
                      ? 'bg-emerald-100 dark:bg-emerald-900' 
                      : 'bg-fuchsia-100 dark:bg-fuchsia-900'
                    }
                  `}>
                    {playlist.type_indicator} {getPlaylistTypeLabel(playlist.type)}
                  </span>
                  
                  <span className={`
                    inline-flex items-center px-2 py-1 rounded-md text-xs font-medium
                    ${getPlaylistSourceColor(playlist.source)} bg-opacity-10
                    ${playlist.source === 'spotify' 
                      ? 'bg-emerald-100 dark:bg-emerald-900' 
                      : 'bg-rose-100 dark:bg-rose-900'
                    }
                  `}>
                    {getPlaylistSourceLabel(playlist.source)}
                  </span>
                </div>

                {/* Stats */}
                <div className="flex items-center space-x-4 mt-2 text-sm text-slate-500 dark:text-slate-400">
                  <div className="flex items-center space-x-1">
                    <PlayCircle className="h-4 w-4" />
                    <span>{playlist.track_count} tracks</span>
                  </div>
                  
                  {(playlist.duration || playlist.duration_ms) && (
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{formatPlaylistDuration(playlist.duration_ms, playlist.duration)}</span>
                    </div>
                  )}
                  
                  {playlist.follower_count && playlist.follower_count > 0 && (
                    <div className="flex items-center space-x-1">
                      <Users className="h-4 w-4" />
                      <span>{playlist.follower_count.toLocaleString()}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 ml-4">
                {/* Selection checkbox */}
                {onToggleSelect && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleSelect();
                    }}
                    className={`
                      w-5 h-5 rounded border-2 flex items-center justify-center transition-colors
                      ${isSelected 
                        ? 'bg-emerald-500 border-emerald-500' 
                        : 'border-slate-300 dark:border-slate-600 hover:border-emerald-400'
                      }
                    `}
                  >
                    {isSelected && (
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    )}
                  </button>
                )}

                {/* Details toggle */}
                <button
                  onClick={handleToggleDetails}
                  className="p-1 rounded-md text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                  title={showDetails ? "Hide details" : "Show details"}
                >
                  {showDetails ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </button>

                {/* External link */}
                {playlist.external_url && (
                  <a
                    href={playlist.external_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="p-1 rounded-md text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
                    title="Open in app"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>

            {/* Description */}
            {playlist.description && (
              <p className="text-sm text-slate-600 dark:text-slate-400 mt-3 line-clamp-2">
                {playlist.description}
              </p>
            )}

            {/* Expanded Details */}
            {showDetails && (
              <div className="mt-4 pt-4 border-t border-slate-200 dark:border-slate-700">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-slate-900 dark:text-slate-100">Visibility:</span>
                    <div className="flex items-center space-x-1 mt-1">
                      {playlist.is_public ? (
                        <>
                          <Eye className="h-3 w-3 text-emerald-600" />
                          <span className="text-emerald-600">Public</span>
                        </>
                      ) : (
                        <>
                          <EyeOff className="h-3 w-3 text-slate-500" />
                          <span className="text-slate-500">Private</span>
                        </>
                      )}
                    </div>
                  </div>
                  
                  {playlist.is_collaborative !== undefined && (
                    <div>
                      <span className="font-medium text-slate-900 dark:text-slate-100">Collaborative:</span>
                      <div className="mt-1">
                        <span className={playlist.is_collaborative ? "text-emerald-600" : "text-slate-500"}>
                          {playlist.is_collaborative ? "Yes" : "No"}
                        </span>
                      </div>
                    </div>
                  )}
                  
                  {playlist.created_at && (
                    <div>
                      <span className="font-medium text-slate-900 dark:text-slate-100">Created:</span>
                      <div className="mt-1 text-slate-600 dark:text-slate-400">
                        {new Date(playlist.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  )}
                  
                  {playlist.last_modified && (
                    <div>
                      <span className="font-medium text-slate-900 dark:text-slate-100">Last Modified:</span>
                      <div className="mt-1 text-slate-600 dark:text-slate-400">
                        {new Date(playlist.last_modified).toLocaleDateString()}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}; 