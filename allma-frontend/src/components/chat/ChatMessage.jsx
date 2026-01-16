/**
 * ChatMessage Component
 * 
 * Renders individual chat messages with role-based styling.
 */

import React, { useState } from 'react';
import { Bot, User, Copy, Check, Database } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import AnimateIn from '../ui/AnimateIn';

const ChatMessage = ({ message, index = 0 }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <AnimateIn
      delay={index * 30}
      className={`flex gap-3 group ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div
        className={`
          shrink-0 w-9 h-9 rounded-xl flex items-center justify-center 
          shadow-md transition-transform group-hover:scale-105
          ${isUser
            ? 'bg-gradient-to-br from-violet-500 to-indigo-600'
            : 'bg-gradient-to-br from-emerald-400 to-cyan-500'
          }
        `}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      {/* Message Content */}
      <div className={`flex-1 max-w-2xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        {/* Header */}
        <div className="flex items-center gap-2 mb-1">
          <span
            className={`text-xs font-semibold ${
              isUser
                ? 'text-violet-600 dark:text-violet-400'
                : 'text-emerald-600 dark:text-emerald-400'
            }`}
          >
            {isUser ? 'You' : 'Allma AI'}
          </span>
          <span className="text-[10px] text-neutral-400">
            {formatTimestamp(message.timestamp)}
          </span>
        </div>

        {/* Bubble */}
        <div
          className={`
            relative rounded-2xl px-4 py-3
            ${isUser
              ? 'bg-gradient-to-br from-violet-500 to-indigo-600 text-white rounded-tr-sm'
              : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 rounded-tl-sm'
            }
            ${message.isError ? 'border-2 border-red-500/50' : ''}
          `}
        >
          {/* Copy Button (for assistant messages) */}
          {!isUser && (
            <button
              onClick={handleCopy}
              className="absolute -top-2 -right-2 p-1.5 rounded-lg bg-white dark:bg-neutral-700 shadow-md opacity-0 group-hover:opacity-100 transition-all hover:scale-110"
              aria-label="Copy message"
            >
              {copied ? (
                <Check className="w-3 h-3 text-emerald-500" />
              ) : (
                <Copy className="w-3 h-3 text-neutral-500" />
              )}
            </button>
          )}

          {/* Content */}
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1.5 prose-headings:my-2">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={oneDark}
                        language={match[1]}
                        PreTag="div"
                        className="rounded-xl my-3 !text-xs"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code
                        className="px-1.5 py-0.5 rounded-md bg-neutral-200 dark:bg-neutral-700 text-xs"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* RAG Context Indicator */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-neutral-500">
            <Database className="w-3 h-3" />
            <span>From {message.sources.length} sources</span>
          </div>
        )}

        {/* Token Usage */}
        {message.usage && (
          <div className="mt-1 text-[10px] text-neutral-400">
            {message.usage.completion_tokens} tokens
          </div>
        )}
      </div>
    </AnimateIn>
  );
};

export default ChatMessage;
