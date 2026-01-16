/**
 * Header Component
 * 
 * Top navigation bar with page title and status.
 */

import React from 'react';
import { Menu } from 'lucide-react';
import Button from '../ui/Button';

const Header = ({
  title,
  subtitle,
  onMenuClick,
  status = 'online',
  actions,
  className = '',
}) => {
  const statusColors = {
    online: 'bg-emerald-500',
    offline: 'bg-red-500',
    connecting: 'bg-amber-500',
    unknown: 'bg-neutral-400',
  };

  const statusLabels = {
    online: 'Online',
    offline: 'Offline',
    connecting: 'Connecting',
    unknown: 'Unknown',
  };

  return (
    <header
      className={`
        h-14 shrink-0 flex items-center justify-between px-4 
        border-b border-neutral-200/80 dark:border-neutral-800 
        bg-white/60 dark:bg-neutral-900/60 backdrop-blur-xl
        ${className}
      `}
    >
      {/* Left side */}
      <div className="flex items-center gap-3">
        {onMenuClick && (
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={onMenuClick}
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </Button>
        )}
        <div>
          <h2 className="font-semibold text-neutral-900 dark:text-white text-sm">
            {title}
          </h2>
          {subtitle && (
            <p className="text-[10px] text-neutral-500">{subtitle}</p>
          )}
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {actions}
        
        {/* Status Indicator */}
        <span className="hidden sm:flex items-center gap-1.5 text-[10px] text-neutral-500 px-2.5 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800">
          <span
            className={`w-1.5 h-1.5 rounded-full ${statusColors[status]} ${
              status === 'online' ? 'animate-pulse' : ''
            }`}
          />
          {statusLabels[status]}
        </span>
      </div>
    </header>
  );
};

export default Header;
