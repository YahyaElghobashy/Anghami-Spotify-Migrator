import React from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

export interface ProgressBarProps {
  value: number; // 0-100
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  label?: string;
  className?: string;
}

const progressVariants = {
  default: 'bg-spotify-500',
  success: 'bg-emerald-500',
  warning: 'bg-amber-500',
  error: 'bg-rose-500',
};

const sizeVariants = {
  sm: 'h-1',
  md: 'h-2',
  lg: 'h-3',
};

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  size = 'md',
  variant = 'default',
  showLabel = false,
  label,
  className,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);

  return (
    <div className={clsx('w-full', className)}>
      {(showLabel || label) && (
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {label}
          </span>
          {showLabel && (
            <span className="text-sm text-slate-500 dark:text-slate-400">
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      
      <div className={clsx(
        sizeVariants[size],
        'w-full rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden'
      )}>
        <motion.div
          className={clsx(
            sizeVariants[size],
            'rounded-full transition-colors duration-300',
            progressVariants[variant]
          )}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ 
            type: "spring", 
            stiffness: 100, 
            damping: 20,
            duration: 0.8 
          }}
        />
      </div>
    </div>
  );
};

export interface CircularProgressProps {
  value: number; // 0-100
  size?: number;
  strokeWidth?: number;
  variant?: 'default' | 'success' | 'warning' | 'error';
  showLabel?: boolean;
  children?: React.ReactNode;
  className?: string;
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  size = 40,
  strokeWidth = 4,
  variant = 'default',
  showLabel = false,
  children,
  className,
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const percentage = Math.min(Math.max(value, 0), 100);
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const colorVariants = {
    default: 'stroke-spotify-500',
    success: 'stroke-emerald-500',
    warning: 'stroke-amber-500',
    error: 'stroke-rose-500',
  };

  return (
    <div className={clsx('relative', className)} style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-slate-200 dark:text-slate-700"
        />
        
        {/* Progress circle */}
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          strokeLinecap="round"
          className={colorVariants[variant]}
          initial={{ strokeDasharray: circumference, strokeDashoffset: circumference }}
          animate={{ strokeDasharray: circumference, strokeDashoffset }}
          transition={{ 
            type: "spring", 
            stiffness: 100, 
            damping: 20,
            duration: 0.8 
          }}
        />
      </svg>
      
      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        {children || (showLabel && (
          <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
            {Math.round(percentage)}%
          </span>
        ))}
      </div>
    </div>
  );
};

export interface StepProgressProps {
  steps: Array<{
    title: string;
    description?: string;
    status: 'pending' | 'current' | 'completed' | 'error';
  }>;
  className?: string;
}

export const StepProgress: React.FC<StepProgressProps> = ({ steps, className }) => {
  return (
    <nav className={clsx('flex flex-col space-y-4', className)} aria-label="Progress">
      {steps.map((step, stepIdx) => {
        const isLast = stepIdx === steps.length - 1;
        
        return (
          <div key={step.title} className="relative flex items-start">
            {/* Step indicator */}
            <div className="flex items-center">
              <div className="flex h-8 w-8 items-center justify-center">
                {step.status === 'completed' ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-spotify-500"
                  >
                    <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </motion.div>
                ) : step.status === 'error' ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-500"
                  >
                    <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                    </svg>
                  </motion.div>
                ) : step.status === 'current' ? (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-spotify-500 bg-white dark:bg-slate-900"
                  >
                    <div className="h-2 w-2 rounded-full bg-spotify-500" />
                  </motion.div>
                ) : (
                  <div className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900">
                    <div className="h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-600" />
                  </div>
                )}
              </div>
            </div>

            {/* Step content */}
            <div className="ml-4 min-w-0 flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-slate-100">
                {step.title}
              </div>
              {step.description && (
                <div className="text-sm text-slate-500 dark:text-slate-400">
                  {step.description}
                </div>
              )}
            </div>

            {/* Connector line */}
            {!isLast && (
              <div className="absolute left-4 top-8 -ml-px h-6 w-0.5 bg-slate-200 dark:bg-slate-700" />
            )}
          </div>
        );
      })}
    </nav>
  );
}; 