/**
 * ChatInput Component
 * 
 * Auto-resizing textarea with send functionality.
 */

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Paperclip } from 'lucide-react';
import Button from '../ui/Button';

const ChatInput = ({
  onSend,
  isLoading = false,
  placeholder = 'Ask me anything...',
  maxHeight = 120,
  showAttachment = false,
  onAttachment,
  disabled = false,
}) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height =
        Math.min(textareaRef.current.scrollHeight, maxHeight) + 'px';
    }
  }, [message, maxHeight]);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSend(message.trim());
      setMessage('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="p-4 md:p-5 bg-gradient-to-t from-neutral-50 dark:from-neutral-950 via-transparent to-transparent">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div
          className={`
            relative bg-white/90 dark:bg-neutral-900/90 backdrop-blur-xl 
            rounded-2xl border border-neutral-200 dark:border-neutral-700 
            shadow-lg transition-all 
            focus-within:ring-2 focus-within:ring-violet-500/40 focus-within:border-violet-500/50
            ${disabled ? 'opacity-50' : ''}
          `}
        >
          {/* Attachment Button (optional) */}
          {showAttachment && (
            <button
              type="button"
              onClick={onAttachment}
              className="absolute left-3 bottom-3 p-1.5 rounded-lg text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 transition-colors"
              aria-label="Attach file"
            >
              <Paperclip className="w-4 h-4" />
            </button>
          )}

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading || disabled}
            rows={1}
            className={`
              w-full bg-transparent py-3.5 text-neutral-900 dark:text-white 
              placeholder-neutral-400 resize-none outline-none text-sm
              ${showAttachment ? 'pl-12 pr-14' : 'px-4 pr-14'}
            `}
            style={{ maxHeight: `${maxHeight}px` }}
          />

          {/* Send Button */}
          <Button
            type="submit"
            variant="primary"
            size="icon"
            disabled={!message.trim() || isLoading || disabled}
            className="absolute right-2 bottom-2"
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>

        {/* Helper Text */}
        <p className="text-[10px] text-neutral-400 text-center mt-1.5">
          Enter to send • Shift+Enter for new line
        </p>
      </form>
    </div>
  );
};

export default ChatInput;
