import React from 'react';
import { clsx } from 'clsx';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ 
    label, 
    error, 
    helperText, 
    leftIcon, 
    rightIcon, 
    className,
    id,
    ...props 
  }, ref) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = Boolean(error);

    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={inputId}
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
          >
            {label}
          </label>
        )}
        
        <div className="relative">
          {leftIcon && (
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <div className="text-slate-400 dark:text-slate-500">
                {leftIcon}
              </div>
            </div>
          )}
          
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              // Base input styles from design guidelines
              'w-full rounded-md border px-3 py-2 text-sm',
              'bg-white dark:bg-slate-800',
              'text-slate-900 dark:text-slate-100',
              'placeholder-slate-400 dark:placeholder-slate-500',
              'focus:outline-none focus:ring-2 focus:ring-offset-2',
              'transition-colors duration-200',
              
              // Conditional styles
              hasError ? [
                'border-rose-600 dark:border-rose-500',
                'focus:ring-rose-500 focus:border-rose-500',
              ] : [
                'border-slate-300 dark:border-slate-600',
                'focus:ring-spotify-500 focus:border-spotify-500',
              ],
              
              // Icon spacing
              leftIcon && 'pl-10',
              rightIcon && 'pr-10',
              
              // Disabled state
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'disabled:bg-slate-50 dark:disabled:bg-slate-900',
              
              className
            )}
            aria-invalid={hasError}
            aria-describedby={
              error ? `${inputId}-error` : 
              helperText ? `${inputId}-helper` : 
              undefined
            }
            {...props}
          />
          
          {rightIcon && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <div className="text-slate-400 dark:text-slate-500">
                {rightIcon}
              </div>
            </div>
          )}
        </div>
        
        {error && (
          <p 
            id={`${inputId}-error`}
            className="mt-2 text-xs text-rose-600 dark:text-rose-400"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p 
            id={`${inputId}-helper`}
            className="mt-2 text-xs text-slate-500 dark:text-slate-400"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
  helperText?: string;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ 
    label, 
    error, 
    helperText, 
    className,
    id,
    ...props 
  }, ref) => {
    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;
    const hasError = Boolean(error);

    return (
      <div className="w-full">
        {label && (
          <label 
            htmlFor={textareaId}
            className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2"
          >
            {label}
          </label>
        )}
        
        <textarea
          ref={ref}
          id={textareaId}
          className={clsx(
            // Base textarea styles
            'w-full rounded-md border px-3 py-2 text-sm',
            'bg-white dark:bg-slate-800',
            'text-slate-900 dark:text-slate-100',
            'placeholder-slate-400 dark:placeholder-slate-500',
            'focus:outline-none focus:ring-2 focus:ring-offset-2',
            'transition-colors duration-200',
            'resize-y',
            
            // Conditional styles
            hasError ? [
              'border-rose-600 dark:border-rose-500',
              'focus:ring-rose-500 focus:border-rose-500',
            ] : [
              'border-slate-300 dark:border-slate-600',
              'focus:ring-spotify-500 focus:border-spotify-500',
            ],
            
            // Disabled state
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'disabled:bg-slate-50 dark:disabled:bg-slate-900',
            
            className
          )}
          aria-invalid={hasError}
          aria-describedby={
            error ? `${textareaId}-error` : 
            helperText ? `${textareaId}-helper` : 
            undefined
          }
          {...props}
        />
        
        {error && (
          <p 
            id={`${textareaId}-error`}
            className="mt-2 text-xs text-rose-600 dark:text-rose-400"
            role="alert"
          >
            {error}
          </p>
        )}
        
        {helperText && !error && (
          <p 
            id={`${textareaId}-helper`}
            className="mt-2 text-xs text-slate-500 dark:text-slate-400"
          >
            {helperText}
          </p>
        )}
      </div>
    );
  }
);

Textarea.displayName = 'Textarea';

// Enhanced Playlist Filters Component for Phase C.3
import { useState, useEffect } from 'react';
import { Search, Filter, SortAsc, SortDesc, X, Music } from 'lucide-react';
import { Button } from './Button';
import { Card, CardContent } from './Card';
import type { PlaylistFilterRequest, PlaylistSources } from '../../api/client';
import { createDefaultFilters } from '../../api/client';

interface EnhancedPlaylistFiltersProps {
  filters: PlaylistFilterRequest;
  onFiltersChange: (filters: PlaylistFilterRequest) => void;
  sources?: PlaylistSources;
  isLoading?: boolean;
  totalResults?: number;
  className?: string;
}

export const EnhancedPlaylistFilters: React.FC<EnhancedPlaylistFiltersProps> = ({
  filters,
  onFiltersChange,
  sources,
  isLoading = false,
  totalResults = 0,
  className = ''
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchInput, setSearchInput] = useState(filters.search_query || '');

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchInput !== filters.search_query) {
        onFiltersChange({
          ...filters,
          search_query: searchInput || undefined,
          page: 1 // Reset to first page on search
        });
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchInput, filters, onFiltersChange]);

  const handleSourceToggle = (source: 'anghami' | 'spotify') => {
    const currentSources = filters.sources || ['anghami', 'spotify'];
    const newSources = currentSources.includes(source)
      ? currentSources.filter(s => s !== source)
      : [...currentSources, source];
    
    onFiltersChange({
      ...filters,
      sources: newSources.length > 0 ? newSources : undefined,
      page: 1
    });
  };

  const handleTypeToggle = (type: 'owned' | 'created' | 'followed') => {
    const currentTypes = filters.types || ['owned', 'created', 'followed'];
    const newTypes = currentTypes.includes(type)
      ? currentTypes.filter(t => t !== type)
      : [...currentTypes, type];
    
    onFiltersChange({
      ...filters,
      types: newTypes.length > 0 ? newTypes : undefined,
      page: 1
    });
  };

  const handleSortChange = (sortBy: 'name' | 'track_count' | 'created_at' | 'last_modified') => {
    const newSortOrder = filters.sort_by === sortBy && filters.sort_order === 'asc' ? 'desc' : 'asc';
    
    onFiltersChange({
      ...filters,
      sort_by: sortBy,
      sort_order: newSortOrder,
      page: 1
    });
  };

  const handleClearFilters = () => {
    const defaultFilters = createDefaultFilters();
    setSearchInput('');
    onFiltersChange(defaultFilters);
  };

  const hasActiveFilters = () => {
    const defaultFilters = createDefaultFilters();
    return (
      searchInput !== '' ||
      JSON.stringify(filters.sources?.sort()) !== JSON.stringify(defaultFilters.sources?.sort()) ||
      JSON.stringify(filters.types?.sort()) !== JSON.stringify(defaultFilters.types?.sort()) ||
      filters.sort_by !== defaultFilters.sort_by ||
      filters.sort_order !== defaultFilters.sort_order
    );
  };

  const activeSourceCount = filters.sources?.length || 2;
  const activeTypeCount = filters.types?.length || 3;

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Main Filter Bar */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0 lg:space-x-4">
            {/* Search */}
            <div className="flex-1 max-w-md">
              <Input
                leftIcon={<Search className="h-4 w-4" />}
                placeholder="Search playlists..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full"
              />
            </div>

            {/* Quick Filters */}
            <div className="flex items-center space-x-3">
              {/* Source filters */}
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">Sources:</span>
                
                {sources?.anghami.available && (
                  <Button
                    variant={filters.sources?.includes('anghami') ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => handleSourceToggle('anghami')}
                    className="relative"
                  >
                    🎼 Anghami
                    {sources.anghami.total_all !== undefined && (
                      <span className="ml-1 text-xs opacity-75">
                        ({sources.anghami.total_all})
                      </span>
                    )}
                  </Button>
                )}
                
                {sources?.spotify.available && (
                  <Button
                    variant={filters.sources?.includes('spotify') ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => handleSourceToggle('spotify')}
                    className="relative"
                  >
                    🎵 Spotify
                    {sources.spotify.total_all !== undefined && (
                      <span className="ml-1 text-xs opacity-75">
                        ({sources.spotify.total_all})
                      </span>
                    )}
                  </Button>
                )}
              </div>

              {/* Advanced filters toggle */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="relative"
              >
                <Filter className="h-4 w-4 mr-1" />
                Advanced
                {hasActiveFilters() && (
                  <div className="absolute -top-1 -right-1 w-2 h-2 bg-emerald-500 rounded-full"></div>
                )}
              </Button>

              {/* Clear filters */}
              {hasActiveFilters() && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFilters}
                  className="text-slate-500 hover:text-slate-700"
                >
                  <X className="h-4 w-4 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </div>

          {/* Results count */}
          <div className="mt-4 text-sm text-slate-600 dark:text-slate-400">
            {isLoading ? (
              <span>Loading playlists...</span>
            ) : (
              <span>
                {totalResults} playlist{totalResults !== 1 ? 's' : ''} found
                {activeSourceCount < 2 && ` from ${filters.sources?.[0] || 'selected'} source`}
                {activeTypeCount < 3 && ` (${filters.types?.join(', ') || 'selected'} only)`}
              </span>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Advanced Filters */}
      {showAdvanced && (
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              <h4 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
                Advanced Filters
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {/* Playlist Types */}
                <div>
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 block">
                    Playlist Types
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: 'created', label: '🎵 Created', desc: 'Playlists you created' },
                      { value: 'owned', label: '🎵 Owned', desc: 'Playlists you own' },
                      { value: 'followed', label: '➕ Followed', desc: 'Playlists you follow' }
                    ].map(({ value, label, desc }) => (
                      <label key={value} className="flex items-start space-x-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={filters.types?.includes(value as any) ?? true}
                          onChange={() => handleTypeToggle(value as any)}
                          className="mt-1 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
                        />
                        <div>
                          <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                            {label}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">
                            {desc}
                          </div>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Sorting */}
                <div>
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 block">
                    Sort By
                  </label>
                  <div className="space-y-2">
                    {[
                      { value: 'name' as const, label: 'Name' },
                      { value: 'track_count' as const, label: 'Track Count' },
                      { value: 'created_at' as const, label: 'Date Created' },
                      { value: 'last_modified' as const, label: 'Last Modified' }
                    ].map(({ value, label }) => (
                      <button
                        key={value}
                        onClick={() => handleSortChange(value)}
                        className={`
                          w-full flex items-center justify-between p-2 rounded-md text-sm transition-colors
                          ${filters.sort_by === value
                            ? 'bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300'
                            : 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                          }
                        `}
                      >
                        <span>{label}</span>
                        {filters.sort_by === value && (
                          filters.sort_order === 'asc' ? (
                            <SortAsc className="h-4 w-4" />
                          ) : (
                            <SortDesc className="h-4 w-4" />
                          )
                        )}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Creator Filter */}
                <div>
                  <label className="text-sm font-medium text-slate-700 dark:text-slate-300 mb-3 block">
                    Filter by Creator
                  </label>
                  <Input
                    placeholder="Creator name..."
                    value={filters.creator_filter || ''}
                    onChange={(e) => onFiltersChange({
                      ...filters,
                      creator_filter: e.target.value || undefined,
                      page: 1
                    })}
                  />
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                    Filter by playlist creator or owner name
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}; 