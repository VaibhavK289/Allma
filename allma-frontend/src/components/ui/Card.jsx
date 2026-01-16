/**
 * Card Component
 * 
 * A flexible card container with various styling options.
 */

import React from 'react';

const Card = ({
  children,
  className = '',
  hover = false,
  glass = false,
  padding = true,
  onClick,
  ...props
}) => {
  const baseStyles = 'rounded-2xl transition-all duration-300';
  
  const bgStyles = glass
    ? 'bg-white/60 dark:bg-neutral-900/60 backdrop-blur-xl border border-white/20 dark:border-neutral-700/50'
    : 'bg-white dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800';
  
  const hoverStyles = hover
    ? 'hover:shadow-lg hover:scale-[1.01] cursor-pointer'
    : 'shadow-sm';
  
  const paddingStyles = padding ? 'p-5' : '';

  return (
    <div
      className={`${baseStyles} ${bgStyles} ${hoverStyles} ${paddingStyles} ${className}`}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card;
