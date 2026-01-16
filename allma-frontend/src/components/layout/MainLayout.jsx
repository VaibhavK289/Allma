/**
 * MainLayout Component
 * 
 * Main application layout with sidebar and content area.
 */

import React from 'react';

const MainLayout = ({ sidebar, header, children, className = '' }) => {
  return (
    <div className="h-screen w-screen flex bg-gradient-to-br from-neutral-50 via-white to-violet-50/30 dark:from-neutral-950 dark:via-neutral-900 dark:to-violet-950/20 overflow-hidden">
      {/* Sidebar */}
      {sidebar}

      {/* Main Content */}
      <div className={`flex-1 flex flex-col min-w-0 ${className}`}>
        {header}
        {children}
      </div>

      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-violet-400/15 rounded-full blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-cyan-400/15 rounded-full blur-3xl" />
      </div>
    </div>
  );
};

export default MainLayout;
