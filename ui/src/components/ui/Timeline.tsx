import React from 'react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Circle, Clock, ArrowRight } from 'lucide-react';

export interface TimelineStep {
  id: number;
  name: string;
  description: string;
  key: string;
  status: 'completed' | 'current' | 'pending';
  details?: string;
}

export interface TimelineProps {
  steps: TimelineStep[];
  currentStep: number;
  onStepClick?: (stepId: number) => void;
  className?: string;
}

export const Timeline: React.FC<TimelineProps> = ({
  steps,
  currentStep,
  onStepClick,
  className
}) => {
  return (
    <div className={clsx('w-full max-w-sm', className)}>
      {/* Timeline Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6"
      >
        <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100 mb-2">
          Migration Progress
        </h3>
        <p className="text-sm text-slate-600 dark:text-slate-400">
          Track your progress through the migration process
        </p>
      </motion.div>

      {/* Timeline Steps */}
      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-6 top-0 bottom-0 w-0.5 bg-slate-200 dark:bg-slate-700" />
        
        {/* Animated Progress Line */}
        <motion.div
          className="absolute left-6 top-0 w-0.5 bg-emerald-500"
          initial={{ height: 0 }}
          animate={{ 
            height: `${((currentStep - 1) / (steps.length - 1)) * 100}%` 
          }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        />

        <AnimatePresence mode="wait">
          {steps.map((step, index) => {
            const isCompleted = step.status === 'completed';
            const isCurrent = step.status === 'current';
            const isClickable = onStepClick && (isCompleted || isCurrent);

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ 
                  delay: index * 0.1,
                  type: "spring",
                  stiffness: 100,
                  damping: 15
                }}
                className="relative flex items-start pb-8 last:pb-0"
              >
                {/* Step Icon */}
                <motion.div
                  whileHover={isClickable ? { scale: 1.1 } : {}}
                  whileTap={isClickable ? { scale: 0.95 } : {}}
                  className={clsx(
                    'relative z-10 flex h-12 w-12 items-center justify-center rounded-full border-2 transition-all duration-300',
                    {
                      'bg-emerald-600 border-emerald-600 text-white shadow-lg': isCompleted,
                      'bg-white dark:bg-slate-900 border-emerald-600 text-emerald-600': isCurrent,
                      'bg-white dark:bg-slate-900 border-slate-300 dark:border-slate-600 text-slate-400': step.status === 'pending',
                      'cursor-pointer hover:border-emerald-500': isClickable,
                    }
                  )}
                  onClick={() => isClickable && onStepClick?.(step.id)}
                >
                  {isCompleted ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : isCurrent ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                      <Clock className="h-6 w-6" />
                    </motion.div>
                  ) : (
                    <Circle className="h-6 w-6" />
                  )}
                  
                  {/* Pulsing ring for current step */}
                  {isCurrent && (
                    <motion.div
                      className="absolute inset-0 rounded-full border-2 border-emerald-400"
                      animate={{ scale: [1, 1.3, 1], opacity: [0.5, 0, 0.5] }}
                      transition={{ duration: 2, repeat: Infinity }}
                    />
                  )}
                </motion.div>

                {/* Step Content */}
                <div className="ml-4 flex-1 min-w-0">
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 + 0.2 }}
                  >
                    {/* Step Title */}
                    <h4 className={clsx(
                      'font-semibold text-sm transition-colors duration-300',
                      {
                        'text-emerald-600 dark:text-emerald-400': isCompleted,
                        'text-slate-900 dark:text-slate-100': isCurrent,
                        'text-slate-500 dark:text-slate-400': step.status === 'pending',
                      }
                    )}>
                      {step.name}
                    </h4>

                    {/* Step Description */}
                    <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                      {step.description}
                    </p>

                    {/* Step Details (for current/completed steps) */}
                    <AnimatePresence>
                      {(isCurrent || isCompleted) && step.details && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          className="mt-2"
                        >
                          <div className="bg-slate-50 dark:bg-slate-800 rounded-md p-2">
                            <p className="text-xs text-slate-700 dark:text-slate-300">
                              {step.details}
                            </p>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Current step indicator */}
                    {isCurrent && (
                      <motion.div
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center mt-2 text-xs text-emerald-600 dark:text-emerald-400"
                      >
                        <ArrowRight className="h-3 w-3 mr-1" />
                        <span className="font-medium">In Progress</span>
                      </motion.div>
                    )}
                  </motion.div>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Timeline Footer */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-700"
      >
        <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>Step {currentStep} of {steps.length}</span>
          <span>{Math.round((currentStep / steps.length) * 100)}% Complete</span>
        </div>
      </motion.div>
    </div>
  );
}; 