/**
 * AnimateIn Component
 * 
 * Wrapper component for fade-in animations.
 */

import React, { useState, useEffect } from 'react';

const AnimateIn = ({
  children,
  delay = 0,
  duration = 500,
  className = '',
  animation = 'fade-up',
}) => {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  const animations = {
    'fade': 'opacity-0 -> opacity-100',
    'fade-up': visible
      ? 'opacity-100 translate-y-0'
      : 'opacity-0 translate-y-4',
    'fade-down': visible
      ? 'opacity-100 translate-y-0'
      : 'opacity-0 -translate-y-4',
    'fade-left': visible
      ? 'opacity-100 translate-x-0'
      : 'opacity-0 translate-x-4',
    'fade-right': visible
      ? 'opacity-100 translate-x-0'
      : 'opacity-0 -translate-x-4',
    'scale': visible
      ? 'opacity-100 scale-100'
      : 'opacity-0 scale-95',
  };

  return (
    <div
      className={`transition-all ease-out ${animations[animation]} ${className}`}
      style={{ transitionDuration: `${duration}ms` }}
    >
      {children}
    </div>
  );
};

export default AnimateIn;
