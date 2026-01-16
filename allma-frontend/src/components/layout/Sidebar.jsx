/**
 * Sidebar Component
 * 
 * Navigation sidebar with conversation list.
 */

import React from 'react';
import {
  Sparkles,
  Plus,
  MessageSquare,
  FileText,
  Settings,
  Moon,
  Sun,
  Trash2,
} from 'lucide-react';
import Button from '../ui/Button';

const Sidebar = ({
  conversations = [],
  activeId,
  onSelect,
  onNew,
  onDelete,
  darkMode,
  toggleDarkMode,
  page,
  setPage,
  isOpen,
  onClose,
}) => {
  const navItems = [
    { id: 'chat', icon: MessageSquare, label: 'Chats' },
    { id: 'documents', icon: FileText, label: 'Documents' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50 w-64 
          bg-white/95 dark:bg-neutral-950/95 backdrop-blur-xl 
          border-r border-neutral-200 dark:border-neutral-800 
          flex flex-col transition-transform duration-300
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="p-4 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
                Allma
              </h1>
              <p className="text-[10px] text-neutral-500 -mt-0.5">AI Studio</p>
            </div>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <Button
            className="w-full"
            onClick={() => {
              onNew?.();
              onClose?.();
            }}
          >
            <Plus className="w-4 h-4" /> New Chat
          </Button>
        </div>

        {/* Navigation */}
        <nav className="px-2 mb-3">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setPage(item.id);
                onClose?.();
              }}
              className={`
                w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all
                ${page === item.id
                  ? 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400'
                  : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
                }
              `}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>

        {/* Conversations List */}
        {page === 'chat' && (
          <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
            <p className="px-3 py-1.5 text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">
              Recent
            </p>
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => {
                  onSelect(conv.id);
                  onClose?.();
                }}
                className={`
                  w-full group relative flex items-start gap-2 p-2.5 rounded-xl text-left transition-all
                  ${activeId === conv.id
                    ? 'bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-800/50'
                    : 'hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-transparent'
                  }
                `}
              >
                <MessageSquare
                  className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                    activeId === conv.id ? 'text-violet-500' : 'text-neutral-400'
                  }`}
                />
                <div className="flex-1 min-w-0">
                  <p
                    className={`text-xs font-medium truncate ${
                      activeId === conv.id
                        ? 'text-violet-700 dark:text-violet-300'
                        : 'text-neutral-700 dark:text-neutral-300'
                    }`}
                  >
                    {conv.title}
                  </p>
                  <p className="text-[10px] text-neutral-500 truncate">
                    {conv.preview}
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete?.(conv.id);
                  }}
                  className="absolute right-1.5 top-1.5 p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-900/30 transition-all"
                  aria-label="Delete conversation"
                >
                  <Trash2 className="w-3 h-3 text-red-500" />
                </button>
              </button>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="p-3 border-t border-neutral-200 dark:border-neutral-800">
          <Button
            variant="ghost"
            className="w-full justify-start"
            onClick={toggleDarkMode}
          >
            {darkMode ? (
              <Sun className="w-4 h-4" />
            ) : (
              <Moon className="w-4 h-4" />
            )}
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </Button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
