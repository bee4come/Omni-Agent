import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X,
  Activity,
  Wallet,
  Users,
  Lock,
  Shield,
  ArrowRight,
  CheckCircle,
  Sparkles
} from 'lucide-react';

interface OnboardingStep {
  icon: React.ElementType;
  title: string;
  description: string;
  color: string;
}

const steps: OnboardingStep[] = [
  {
    icon: Wallet,
    title: 'Treasury Management',
    description: 'Monitor your MNEE balance and track spending across all agents in real-time.',
    color: 'text-emerald-400',
  },
  {
    icon: Users,
    title: 'Agent Fleet',
    description: 'Manage your AI agents with individual budgets, priorities, and capabilities.',
    color: 'text-indigo-400',
  },
  {
    icon: Lock,
    title: 'Trustless Escrow',
    description: 'Secure Agent-to-Agent transactions with automatic verification and dispute resolution.',
    color: 'text-amber-400',
  },
  {
    icon: Shield,
    title: 'Policy Enforcement',
    description: 'Automatic budget limits, risk scoring, and transaction auditing for every operation.',
    color: 'text-purple-400',
  },
];

interface OnboardingModalProps {
  onComplete: () => void;
}

export const OnboardingModal = ({ onComplete }: OnboardingModalProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(true);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handleComplete = () => {
    setIsVisible(false);
    localStorage.setItem('mnee-onboarding-complete', 'true');
    setTimeout(onComplete, 300);
  };

  const handleSkip = () => {
    handleComplete();
  };

  const CurrentIcon = steps[currentStep].icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.9, opacity: 0, y: 20 }}
            className="bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg overflow-hidden"
          >
            {/* Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
                  <Activity className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-lg font-bold text-white">Welcome to MNEE Nexus</h2>
                  <p className="text-xs text-slate-500">AI Agent Payment Orchestration</p>
                </div>
              </div>
              <button
                onClick={handleSkip}
                className="p-2 text-slate-400 hover:text-white transition-colors"
                aria-label="Skip onboarding"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Content */}
            <div className="p-8">
              <AnimatePresence mode="wait">
                <motion.div
                  key={currentStep}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.2 }}
                  className="text-center"
                >
                  <div className={`mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-6 bg-slate-800 ${steps[currentStep].color}`}>
                    <CurrentIcon className="w-8 h-8" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-3">
                    {steps[currentStep].title}
                  </h3>
                  <p className="text-slate-400 text-sm leading-relaxed">
                    {steps[currentStep].description}
                  </p>
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Progress dots */}
            <div className="flex justify-center gap-2 pb-4">
              {steps.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentStep(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentStep
                      ? 'w-6 bg-indigo-500'
                      : index < currentStep
                      ? 'bg-indigo-500/50'
                      : 'bg-slate-700'
                  }`}
                  aria-label={`Go to step ${index + 1}`}
                />
              ))}
            </div>

            {/* Footer */}
            <div className="p-6 border-t border-slate-800 flex items-center justify-between">
              <button
                onClick={handleSkip}
                className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
              >
                Skip tutorial
              </button>
              <button
                onClick={handleNext}
                className="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium text-white transition-colors"
              >
                {currentStep < steps.length - 1 ? (
                  <>
                    Next
                    <ArrowRight className="w-4 h-4" />
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Get Started
                  </>
                )}
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

// Hook to check if onboarding should be shown
export const useOnboarding = () => {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    const completed = localStorage.getItem('mnee-onboarding-complete');
    if (!completed) {
      // Small delay to prevent flash
      setTimeout(() => setShowOnboarding(true), 500);
    }
  }, []);

  const completeOnboarding = () => {
    setShowOnboarding(false);
  };

  return { showOnboarding, completeOnboarding };
};

export default OnboardingModal;
