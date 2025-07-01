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