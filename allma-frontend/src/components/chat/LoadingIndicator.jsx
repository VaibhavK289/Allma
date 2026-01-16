/**
 * LoadingIndicator Component
 * 
 * Shows AI is thinking/processing.
 */

import React from 'react';
import { Bot } from 'lucide-react';

const LoadingIndicator = () => {
  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center animate-pulse">
        <Bot className="w-4 h-4 text-white" />
      </div>

      {/* Content */}
      <div className="flex-1 max-w-2xl">
        <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1">
          Allma AI
        </div>
        <div className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl rounded-tl-sm px-4 py-3 inline-flex items-center gap-2">
          {/* Animated dots */}
          <div className="flex gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce"
                style={{ animationDelay: `${i * 150}ms` }}
              />
            ))}
          </div>
          <span className="text-xs text-neutral-500">Thinking...</span>
        </div>
      </div>
    </div>
  );
};

export default LoadingIndicator;
