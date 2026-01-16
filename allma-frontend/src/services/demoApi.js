/**
 * Demo API Service
 * 
 * Simulates backend responses for portfolio/demo purposes.
 * Used when no backend is available or in demo mode.
 */

const DEMO_RESPONSES = [
  "Hello! I'm Allma AI, a RAG-powered assistant. This is a demo mode showcasing the application's capabilities. In production, I connect to local LLMs via Ollama for private, offline AI conversations.",
  "Great question! This application uses **Retrieval-Augmented Generation (RAG)** to enhance AI responses with your own documents. Key features:\n\n- 🔒 **Privacy-first**: All processing happens locally\n- 📚 **Document ingestion**: Upload PDFs, docs, and text files\n- 🧠 **Vector search**: ChromaDB for semantic retrieval\n- ⚡ **Fast inference**: Ollama with optimized models",
  "The tech stack includes:\n\n**Frontend:**\n- React 18 + Vite\n- TailwindCSS\n- Responsive design\n\n**Backend:**\n- FastAPI (Python)\n- ChromaDB vector store\n- Ollama LLM integration\n\n**Deployment:**\n- Docker & Kubernetes ready\n- CI/CD with GitHub Actions",
  "I can help with various tasks:\n\n1. **Code assistance** - Explain, debug, and generate code\n2. **Document Q&A** - Answer questions about uploaded documents\n3. **Research** - Summarize and analyze information\n4. **Writing** - Draft emails, reports, and content\n\nWhat would you like to explore?",
  "This demo showcases the UI and interaction patterns. In the full version:\n\n- Connect to **Ollama** for local LLM inference\n- Use **Groq API** for cloud-based fast inference\n- Ingest documents for **RAG-powered** responses\n- Maintain **conversation history** with context",
];

const DEMO_MODELS = [
  { name: 'deepseek-r1:latest', size: 5200000000, modified_at: new Date().toISOString() },
  { name: 'gemma2:9b', size: 5400000000, modified_at: new Date().toISOString() },
  { name: 'llama3.2:latest', size: 4700000000, modified_at: new Date().toISOString() },
  { name: 'nomic-embed-text:latest', size: 274000000, modified_at: new Date().toISOString() },
];

const DEMO_DOCUMENTS = [
  { id: '1', filename: 'project_documentation.pdf', chunk_count: 45, created_at: new Date().toISOString() },
  { id: '2', filename: 'api_reference.md', chunk_count: 23, created_at: new Date().toISOString() },
  { id: '3', filename: 'user_guide.docx', chunk_count: 67, created_at: new Date().toISOString() },
];

class DemoApiService {
  constructor() {
    this.responseIndex = 0;
    this.isDemoMode = true;
  }

  async delay(ms = 500) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async sendMessage(message, options = {}) {
    // Simulate network delay
    await this.delay(800 + Math.random() * 1200);

    const response = DEMO_RESPONSES[this.responseIndex % DEMO_RESPONSES.length];
    this.responseIndex++;

    return {
      id: `demo-${Date.now()}`,
      conversationId: options.conversationId || 'demo-conversation',
      content: response,
      model: 'demo-mode',
      sources: options.useRag ? [
        { document: 'demo_doc.pdf', relevance: 0.95, snippet: 'Sample relevant content...' }
      ] : [],
      usage: { prompt_tokens: 50, completion_tokens: 150 },
      isDemo: true,
    };
  }

  async getModels() {
    await this.delay(300);
    return {
      models: DEMO_MODELS,
      current_model: 'deepseek-r1:latest',
    };
  }

  async getDocuments() {
    await this.delay(300);
    return {
      documents: DEMO_DOCUMENTS,
      total: DEMO_DOCUMENTS.length,
    };
  }

  async uploadDocument(file) {
    await this.delay(1500);
    return {
      success: true,
      document_id: `demo-${Date.now()}`,
      filename: file.name,
      chunk_count: Math.floor(Math.random() * 50) + 10,
      message: 'Document processed successfully (demo mode)',
    };
  }

  async deleteDocument(documentId) {
    await this.delay(500);
    return { success: true, message: 'Document deleted (demo mode)' };
  }

  async checkHealth() {
    await this.delay(200);
    return {
      status: 'demo',
      version: '2.0.0-demo',
      services: [
        { name: 'frontend', status: 'healthy' },
        { name: 'demo-mode', status: 'active' },
      ],
      message: 'Running in demo mode - connect backend for full functionality',
    };
  }

  async searchDocuments(query) {
    await this.delay(600);
    return {
      results: [
        { document: 'demo_doc.pdf', snippet: `Results for "${query}"...`, score: 0.92 },
      ],
      total: 1,
    };
  }

  async getConversations() {
    await this.delay(300);
    return {
      conversations: [],
    };
  }

  async clearConversation(conversationId) {
    await this.delay(300);
    return { success: true };
  }
}

export const demoApi = new DemoApiService();
export default DemoApiService;
