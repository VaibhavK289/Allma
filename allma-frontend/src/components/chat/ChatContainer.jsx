/**
 * ChatContainer Component
 * 
 * Container for chat messages with auto-scroll.
 */

import React, { useRef, useEffect } from 'react';
import ChatMessage from './ChatMessage';
import LoadingIndicator from './LoadingIndicator';
import EmptyState from './EmptyState';

const ChatContainer = ({
  messages = [],
  isLoading = false,
  streamingContent = '',
  onNewChat,
  className = '',
}) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingContent]);

  if (messages.length === 0) {
    return <EmptyState onNewChat={onNewChat} />;
  }

  return (
    <div className={`flex-1 overflow-y-auto px-4 py-5 space-y-4 ${className}`}>
      <div className="max-w-3xl mx-auto space-y-4">
        {/* Messages */}
        {messages.map((msg, i) => (
          <ChatMessage key={`${msg.timestamp}-${i}`} message={msg} index={i} />
        ))}

        {/* Streaming Content */}
        {streamingContent && (
          <ChatMessage
            message={{
              role: 'assistant',
              content: streamingContent,
              timestamp: Date.now(),
            }}
            index={messages.length}
          />
        )}

        {/* Loading Indicator */}
        {isLoading && !streamingContent && <LoadingIndicator />}

        {/* Scroll anchor */}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};

export default ChatContainer;
