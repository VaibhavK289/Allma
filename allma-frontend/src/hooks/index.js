/**
 * Custom React Hooks
 * 
 * Reusable hooks for state management, side effects, and API interactions.
 */

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import api from '../services/api';

// ============================================
// Local Storage Hook
// ============================================

export function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}

// ============================================
// Dark Mode Hook
// ============================================

export function useDarkMode() {
  const [darkMode, setDarkMode] = useLocalStorage('darkMode', true);

  useEffect(() => {
    const root = document.documentElement;
    if (darkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = useCallback(() => {
    setDarkMode((prev) => !prev);
  }, [setDarkMode]);

  return [darkMode, toggleDarkMode];
}

// ============================================
// API Health Check Hook
// ============================================

export function useHealthCheck(interval = 30000) {
  const [status, setStatus] = useState('unknown');
  const [lastCheck, setLastCheck] = useState(null);
  const [error, setError] = useState(null);

  const checkHealth = useCallback(async () => {
    try {
      const response = await api.healthCheck();
      setStatus(response.status);
      setError(null);
    } catch (err) {
      setStatus('unhealthy');
      setError(err.message);
    }
    setLastCheck(new Date());
  }, []);

  useEffect(() => {
    checkHealth();
    const intervalId = setInterval(checkHealth, interval);
    return () => clearInterval(intervalId);
  }, [checkHealth, interval]);

  return { status, lastCheck, error, refresh: checkHealth };
}

// ============================================
// Chat Hook
// ============================================

export function useChat(settings) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');
  const abortControllerRef = useRef(null);

  const sendMessage = useCallback(async (content, conversationId) => {
    if (!content.trim()) return;

    setError(null);
    setIsLoading(true);
    
    const userMessage = {
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      // Update API base URL if changed
      if (settings?.apiUrl) {
        api.setBaseUrl(settings.apiUrl);
      }

      const response = await api.sendMessage(content, {
        conversationId,
        useRag: settings?.useRAG ?? true,
        model: settings?.model,
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.content,
        timestamp: Date.now(),
        sources: response.sources,
        usage: response.usage,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      return response;
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: `⚠️ Error: ${err.message}. Make sure the backend is running.`,
        timestamp: Date.now(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [settings]);

  const sendStreamingMessage = useCallback(async (content, conversationId) => {
    if (!content.trim()) return;

    setError(null);
    setIsLoading(true);
    setStreamingContent('');

    const userMessage = {
      role: 'user',
      content,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      if (settings?.apiUrl) {
        api.setBaseUrl(settings.apiUrl);
      }

      await api.streamMessage(content, {
        conversationId,
        useRag: settings?.useRAG ?? true,
        model: settings?.model,
        onToken: (token) => {
          setStreamingContent((prev) => prev + token);
        },
        onComplete: (fullContent) => {
          const assistantMessage = {
            role: 'assistant',
            content: fullContent,
            timestamp: Date.now(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setStreamingContent('');
          setIsLoading(false);
        },
        onError: (err) => {
          setError(err);
          setIsLoading(false);
        },
      });
    } catch (err) {
      setError(err);
      setIsLoading(false);
      throw err;
    }
  }, [settings]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  return {
    messages,
    setMessages,
    isLoading,
    error,
    streamingContent,
    sendMessage,
    sendStreamingMessage,
    clearMessages,
    cancelStream,
  };
}

// ============================================
// Models Hook
// ============================================

export function useModels() {
  const [models, setModels] = useState([]);
  const [currentModel, setCurrentModel] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchModels = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.listModels();
      setModels(response.models || []);
      setCurrentModel(response.current_model);
    } catch (err) {
      setError(err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const switchModel = useCallback(async (modelName) => {
    setIsLoading(true);
    setError(null);
    try {
      await api.switchModel(modelName);
      setCurrentModel(modelName);
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  return {
    models,
    currentModel,
    isLoading,
    error,
    fetchModels,
    switchModel,
  };
}

// ============================================
// Documents Hook
// ============================================

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);

  const uploadDocument = useCallback(async (file) => {
    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const response = await api.uploadDocument(file);
      
      const newDoc = {
        id: Date.now().toString(),
        name: file.name,
        size: file.size,
        chunksCreated: response.chunks_created,
        uploadedAt: new Date(),
        status: 'indexed',
      };

      setDocuments((prev) => [...prev, newDoc]);
      setUploadProgress(100);
      return response;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setIsUploading(false);
    }
  }, []);

  const uploadMultiple = useCallback(async (files) => {
    const results = [];
    for (const file of files) {
      try {
        const result = await uploadDocument(file);
        results.push({ file: file.name, success: true, result });
      } catch (err) {
        results.push({ file: file.name, success: false, error: err });
      }
    }
    return results;
  }, [uploadDocument]);

  const deleteDocument = useCallback(async (docId) => {
    try {
      await api.deleteDocument(docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      setError(err);
      throw err;
    }
  }, []);

  const clearAll = useCallback(() => {
    setDocuments([]);
  }, []);

  return {
    documents,
    isUploading,
    uploadProgress,
    error,
    uploadDocument,
    uploadMultiple,
    deleteDocument,
    clearAll,
  };
}

// ============================================
// Search Hook
// ============================================

export function useSearch() {
  const [results, setResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (query, options = {}) => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const response = await api.search(query, options);
      setResults(response.results || []);
      return response;
    } catch (err) {
      setError(err);
      setResults([]);
      throw err;
    } finally {
      setIsSearching(false);
    }
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
  }, []);

  return {
    results,
    isSearching,
    error,
    search,
    clearResults,
  };
}

// ============================================
// Debounce Hook
// ============================================

export function useDebounce(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// ============================================
// Keyboard Shortcut Hook
// ============================================

export function useKeyboardShortcut(key, callback, modifiers = {}) {
  useEffect(() => {
    const handler = (event) => {
      const { ctrl = false, shift = false, alt = false, meta = false } = modifiers;
      
      if (
        event.key.toLowerCase() === key.toLowerCase() &&
        event.ctrlKey === ctrl &&
        event.shiftKey === shift &&
        event.altKey === alt &&
        event.metaKey === meta
      ) {
        event.preventDefault();
        callback(event);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [key, callback, modifiers]);
}

// ============================================
// Click Outside Hook
// ============================================

export function useClickOutside(ref, callback) {
  useEffect(() => {
    const handler = (event) => {
      if (ref.current && !ref.current.contains(event.target)) {
        callback(event);
      }
    };

    document.addEventListener('mousedown', handler);
    document.addEventListener('touchstart', handler);
    
    return () => {
      document.removeEventListener('mousedown', handler);
      document.removeEventListener('touchstart', handler);
    };
  }, [ref, callback]);
}

// ============================================
// Window Size Hook
// ============================================

export function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const handler = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  const isMobile = useMemo(() => size.width < 768, [size.width]);
  const isTablet = useMemo(() => size.width >= 768 && size.width < 1024, [size.width]);
  const isDesktop = useMemo(() => size.width >= 1024, [size.width]);

  return { ...size, isMobile, isTablet, isDesktop };
}
