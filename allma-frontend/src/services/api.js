/**
 * API Service Layer
 * 
 * Centralized API communication with the backend.
 * Handles all HTTP requests, error handling, and response transformation.
 * Falls back to demo mode when backend is unavailable.
 */

import { demoApi } from './demoApi';

const DEFAULT_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  constructor(baseUrl = DEFAULT_API_URL) {
    this.baseUrl = baseUrl;
    this.isDemoMode = false;
    this.demoApi = demoApi;
  }

  setBaseUrl(url) {
    this.baseUrl = url;
  }

  async checkBackendAvailable() {
    try {
      const response = await fetch(`${this.baseUrl}/health/`, { 
        method: 'GET',
        signal: AbortSignal.timeout(3000)
      });
      return response.ok;
    } catch {
      return false;
    }
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new ApiError(
          error.message || `HTTP ${response.status}`,
          response.status,
          error.code
        );
      }

      // Handle streaming responses
      if (options.stream) {
        return response;
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        error.message || 'Network error',
        0,
        'NETWORK_ERROR'
      );
    }
  }

  // ============================================
  // Chat Endpoints
  // ============================================

  async sendMessage(message, options = {}) {
    // Check if we should use demo mode
    if (this.isDemoMode || !(await this.checkBackendAvailable())) {
      this.isDemoMode = true;
      return this.demoApi.sendMessage(message, options);
    }

    const {
      conversationId,
      useRag = true,
      model,
      stream = false,
    } = options;

    try {
      const response = await this.request('/chat/', {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          use_rag: useRag,
          model,
          stream,
        }),
      });

      return {
        id: response.id,
        conversationId: response.conversation_id,
        content: response.content,
        model: response.model,
        sources: response.sources || [],
        usage: response.usage,
      };
    } catch (error) {
      // Fall back to demo mode on error
      this.isDemoMode = true;
      return this.demoApi.sendMessage(message, options);
    }
  }

  async streamMessage(message, options = {}) {
    const {
      conversationId,
      useRag = true,
      model,
      onToken,
      onComplete,
      onError,
    } = options;

    try {
      const response = await this.request('/chat/stream', {
        method: 'POST',
        body: JSON.stringify({
          message,
          conversation_id: conversationId,
          use_rag: useRag,
          model,
          stream: true,
        }),
        stream: true,
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          onComplete?.(fullContent);
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') {
              onComplete?.(fullContent);
              return;
            }
            fullContent += data;
            onToken?.(data);
          }
        }
      }
    } catch (error) {
      onError?.(error);
      throw error;
    }
  }

  async getConversation(conversationId) {
    return this.request(`/chat/conversation/${conversationId}`);
  }

  async deleteConversation(conversationId) {
    return this.request(`/chat/conversation/${conversationId}`, {
      method: 'DELETE',
    });
  }

  async listConversations() {
    return this.request('/chat/conversations');
  }

  // ============================================
  // RAG Endpoints
  // ============================================

  async ingestText(text, source = 'direct_input', metadata = {}) {
    return this.request('/rag/ingest', {
      method: 'POST',
      body: JSON.stringify({
        text,
        source,
        metadata,
      }),
    });
  }

  async ingestFile(filePath, metadata = {}) {
    return this.request('/rag/ingest', {
      method: 'POST',
      body: JSON.stringify({
        file_path: filePath,
        metadata,
      }),
    });
  }

  async uploadDocument(file, source = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (source) {
      formData.append('source', source);
    }

    return this.request('/rag/ingest/upload', {
      method: 'POST',
      body: formData,
      headers: {}, // Let browser set Content-Type for FormData
    });
  }

  async search(query, options = {}) {
    const { topK = 5, threshold, filterSource } = options;
    
    return this.request('/rag/search', {
      method: 'POST',
      body: JSON.stringify({
        query,
        top_k: topK,
        threshold,
        filter_source: filterSource,
      }),
    });
  }

  async getDocuments() {
    if (this.isDemoMode) {
      return this.demoApi.getDocuments();
    }
    try {
      return await this.request('/rag/documents');
    } catch {
      this.isDemoMode = true;
      return this.demoApi.getDocuments();
    }
  }

  async deleteDocument(documentId) {
    return this.request(`/rag/documents/${documentId}`, {
      method: 'DELETE',
    });
  }

  async getRAGStats() {
    return this.request('/rag/stats');
  }

  // ============================================
  // Model Endpoints
  // ============================================

  async listModels() {
    if (this.isDemoMode) {
      return this.demoApi.getModels();
    }
    try {
      return await this.request('/models/');
    } catch {
      this.isDemoMode = true;
      return this.demoApi.getModels();
    }
  }

  async switchModel(modelName) {
    return this.request('/models/switch', {
      method: 'POST',
      body: JSON.stringify({ model: modelName }),
    });
  }

  async pullModel(modelName) {
    return this.request('/models/pull', {
      method: 'POST',
      body: JSON.stringify({ model: modelName }),
    });
  }

  // ============================================
  // Health Endpoints
  // ============================================

  async healthCheck() {
    if (this.isDemoMode) {
      return this.demoApi.checkHealth();
    }
    try {
      return await this.request('/health/');
    } catch {
      this.isDemoMode = true;
      return this.demoApi.checkHealth();
    }
  }

  async liveness() {
    return this.request('/health/live');
  }

  async readiness() {
    return this.request('/health/ready');
  }

  async getConfig() {
    return this.request('/health/config');
  }
}

/**
 * Custom API Error class
 */
class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }

  isNetworkError() {
    return this.status === 0;
  }

  isServerError() {
    return this.status >= 500;
  }

  isClientError() {
    return this.status >= 400 && this.status < 500;
  }

  isNotFound() {
    return this.status === 404;
  }

  isRateLimited() {
    return this.status === 429;
  }
}

// Singleton instance
const api = new ApiService();

export { api, ApiService, ApiError };
export default api;
