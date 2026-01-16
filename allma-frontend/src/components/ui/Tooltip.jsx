/**
 * Tooltip Component
 * 
 * Lightweight tooltip for providing additional context.
 */

import React, { useState } from 'react';

const Tooltip = ({
  children,
  content,
  position = 'top',
  delay = 300,
  className = '',
}) => {
  const [visible, setVisible] = useState(false);
  const [timeoutId, setTimeoutId] = useState(null);

  const showTooltip = () => {
    const id = setTimeout(() => setVisible(true), delay);
    setTimeoutId(id);
  };

  const hideTooltip = () => {
    if (timeoutId) clearTimeout(timeoutId);
    setVisible(false);
  };

  const positions = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  const arrows = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-neutral-900 dark:border-t-neutral-700 border-x-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-neutral-900 dark:border-b-neutral-700 border-x-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-neutral-900 dark:border-l-neutral-700 border-y-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-neutral-900 dark:border-r-neutral-700 border-y-transparent border-l-transparent',
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      
      {visible && content && (
        <div
          className={`
            absolute z-50 ${positions[position]}
            px-2 py-1 text-xs font-medium
            bg-neutral-900 dark:bg-neutral-700 
            text-white rounded-lg
            whitespace-nowrap
            pointer-events-none
            animate-fade-in
            ${className}
          `}
          role="tooltip"
        >
          {content}
          <div
            className={`absolute w-0 h-0 border-4 ${arrows[position]}`}
          />
        </div>
      )}
    </div>
  );
};

export default Tooltip;
