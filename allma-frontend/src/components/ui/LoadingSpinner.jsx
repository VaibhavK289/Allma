/**
 * LoadingSpinner Component
 * 
 * Animated loading indicator.
 */

import React from 'react';

const LoadingSpinner = ({
  size = 'md',
  className = '',
  color = 'primary',
}) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12',
  };

  const colors = {
    primary: 'text-violet-600',
    secondary: 'text-neutral-600',
    white: 'text-white',
    current: 'text-current',
  };

  return (
    <svg
      className={`animate-spin ${sizes[size]} ${colors[color]} ${className}`}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
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
  );
};

// Dots variant
export const LoadingDots = ({ className = '' }) => (
  <div className={`flex gap-1 ${className}`}>
    {[0, 1, 2].map((i) => (
      <span
        key={i}
        className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"
        style={{ animationDelay: `${i * 150}ms` }}
      />
    ))}
  </div>
);

// Pulse variant  
export const LoadingPulse = ({ className = '' }) => (
  <div className={`flex items-center gap-2 ${className}`}>
    <div className="w-2 h-2 bg-violet-500 rounded-full animate-pulse" />
    <span className="text-sm text-neutral-500">Loading...</span>
  </div>
);

export default LoadingSpinner;
