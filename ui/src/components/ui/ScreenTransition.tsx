import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface ScreenTransitionProps {
  children: React.ReactNode;
  screenKey: string;
  className?: string;
}

export const ScreenTransition: React.FC<ScreenTransitionProps> = ({
  children,
  screenKey,
  className = ''
}) => {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={screenKey}
        initial={{ 
          opacity: 0, 
          y: 50, // Fade in from bottom
          scale: 0.95 
        }}
        animate={{ 
          opacity: 1, 
          y: 0,
          scale: 1 
        }}
        exit={{ 
          opacity: 0, 
          y: -50, // Fade out to top
          scale: 0.95 
        }}
        transition={{
          type: "spring",
          stiffness: 100,
          damping: 20,
          mass: 1,
          duration: 0.4
        }}
        className={className}
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}; 