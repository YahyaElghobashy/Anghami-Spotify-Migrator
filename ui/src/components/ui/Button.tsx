import React from 'react';
import { clsx } from 'clsx';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  className,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  ...props
}) => {
  const isDisabled = disabled || loading;

  const baseClasses = clsx(
    // Base styles from design guidelines
    'inline-flex items-center px-4 py-2 rounded-md font-medium transition-all duration-300 ease-in-out',
    'focus:outline-none focus:ring-2 focus:ring-offset-2',
    'disabled:opacity-50 disabled:cursor-not-allowed',
    'active:scale-95',
    
    // Size variants
    {
      'px-3 py-1.5 text-sm': size === 'sm',
      'px-4 py-2 text-base': size === 'md',
      'px-6 py-3 text-lg': size === 'lg',
    },
    
    // Variant styles following design guidelines exactly
    {
      // Primary - Spotify green as specified
      'bg-emerald-600 hover:bg-emerald-700 focus:ring-emerald-500 text-white': variant === 'primary',
      
      // Secondary - as specified in guidelines
      'bg-slate-100 text-slate-900 dark:bg-slate-700 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-slate-600 focus:ring-slate-500': variant === 'secondary',
      
      // Ghost - as specified in guidelines
      'bg-transparent hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 focus:ring-slate-500': variant === 'ghost',
      
      // Destructive - as specified in guidelines
      'bg-rose-600 hover:bg-rose-700 focus:ring-rose-500 text-white': variant === 'destructive',
    },
    
    className
  );

  return (
    <button
      className={baseClasses}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}; 