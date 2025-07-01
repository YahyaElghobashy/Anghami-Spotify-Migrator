import React from 'react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';

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