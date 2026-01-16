import { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Menu, X, Sparkles, FileText, Database, Settings, Moon, Sun, Plus, Send, 
  Loader2, Copy, Check, Trash2, Upload, Search, MessageSquare, Zap, Shield, 
  Bot, User, ExternalLink, ChevronRight, Home, Folder, Clock, BarChart3
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './App.css';

// ============================================================================
// CONFIGURATION
// ============================================================================
const API_BASE_URL = 'http://localhost:8000';

const defaultSettings = {
  model: 'deepseek-r1:latest',
  embeddingModel: 'nomic-embed-text:latest',
  useRAG: true,
  topK: 5,
  apiUrl: API_BASE_URL,
};

const models = [
  { value: 'deepseek-r1:latest', label: 'DeepSeek R1', size: '5.2GB', desc: 'Best for reasoning' },
  { value: 'gemma2:9b', label: 'Gemma 2 9B', size: '5.4GB', desc: 'Balanced performance' },
  { value: 'qwen2.5-coder:7b', label: 'Qwen 2.5 Coder', size: '4.7GB', desc: 'Optimized for code' },
];

// ============================================================================
// HOOKS
// ============================================================================
const useLocalStorage = (key, initialValue) => {
  const [value, setValue] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });
  
  useEffect(() => {
    localStorage.setItem(key, JSON.stringify(value));
  }, [key, value]);
  
  return [value, setValue];
};

const useDarkMode = () => {
  const [darkMode, setDarkMode] = useLocalStorage('darkMode', true);
  
  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  }, [darkMode]);
  
  return [darkMode, () => setDarkMode(!darkMode)];
};

// ============================================================================
// UTILITY COMPONENTS
// ============================================================================
const AnimateIn = ({ children, delay = 0, className = '' }) => {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);
  
  return (
    <div className={`transition-all duration-500 ease-out ${visible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'} ${className}`}>
      {children}
    </div>
  );
};

const Button = ({ children, variant = 'primary', size = 'md', className = '', ...props }) => {
  const variants = {
    primary: 'bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-lg shadow-violet-500/25 hover:shadow-xl hover:shadow-violet-500/30 hover:from-violet-500 hover:to-indigo-500 active:scale-[0.98]',
    secondary: 'bg-white/80 dark:bg-neutral-800/80 text-neutral-900 dark:text-white border border-neutral-200 dark:border-neutral-700 hover:bg-neutral-50 dark:hover:bg-neutral-700/80',
    ghost: 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800 hover:text-neutral-900 dark:hover:text-white',
    danger: 'bg-red-500/10 text-red-600 dark:text-red-400 hover:bg-red-500/20',
  };
  const sizes = {
    sm: 'px-3 py-1.5 text-xs rounded-xl gap-1.5',
    md: 'px-4 py-2.5 text-sm rounded-xl gap-2',
    lg: 'px-6 py-3 text-base rounded-2xl gap-2',
    icon: 'p-2.5 rounded-xl',
  };
  
  return (
    <button 
      className={`font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center justify-center ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

const Card = ({ children, className = '', hover = false, glass = false }) => (
  <div className={`rounded-2xl p-5 transition-all duration-300 ${
    glass ? 'bg-white/60 dark:bg-neutral-900/60 backdrop-blur-xl border border-white/20 dark:border-neutral-700/50' 
          : 'bg-white dark:bg-neutral-900 border border-neutral-200/60 dark:border-neutral-800'
  } ${hover ? 'hover:shadow-lg hover:scale-[1.01] cursor-pointer' : 'shadow-sm'} ${className}`}>
    {children}
  </div>
);

const Badge = ({ children, variant = 'default' }) => {
  const variants = {
    default: 'bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400',
    success: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400',
    warning: 'bg-amber-100 dark:bg-amber-900/30 text-amber-600 dark:text-amber-400',
    primary: 'bg-violet-100 dark:bg-violet-900/30 text-violet-600 dark:text-violet-400',
  };
  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${variants[variant]}`}>
      {children}
    </span>
  );
};

// ============================================================================
// CHAT MESSAGE
// ============================================================================
const ChatMessage = ({ message, index }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  
  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <AnimateIn delay={index * 30} className={`flex gap-3 group ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`shrink-0 w-9 h-9 rounded-xl flex items-center justify-center shadow-md transition-transform group-hover:scale-105 ${
        isUser ? 'bg-gradient-to-br from-violet-500 to-indigo-600' : 'bg-gradient-to-br from-emerald-400 to-cyan-500'
      }`}>
        {isUser ? <User className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
      </div>
      
      <div className={`flex-1 max-w-2xl ${isUser ? 'flex flex-col items-end' : ''}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className={`text-xs font-semibold ${isUser ? 'text-violet-600 dark:text-violet-400' : 'text-emerald-600 dark:text-emerald-400'}`}>
            {isUser ? 'You' : 'Allma AI'}
          </span>
          <span className="text-[10px] text-neutral-400">
            {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>
        
        <div className={`relative rounded-2xl px-4 py-3 ${
          isUser 
            ? 'bg-gradient-to-br from-violet-500 to-indigo-600 text-white rounded-tr-sm' 
            : 'bg-neutral-100 dark:bg-neutral-800 text-neutral-900 dark:text-neutral-100 rounded-tl-sm'
        }`}>
          {!isUser && (
            <button onClick={handleCopy} className="absolute -top-2 -right-2 p-1.5 rounded-lg bg-white dark:bg-neutral-700 shadow-md opacity-0 group-hover:opacity-100 transition-all hover:scale-110">
              {copied ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3 text-neutral-500" />}
            </button>
          )}
          
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:my-1.5 prose-headings:my-2">
              <ReactMarkdown
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter style={oneDark} language={match[1]} PreTag="div" className="rounded-xl my-3 !text-xs" {...props}>
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="px-1.5 py-0.5 rounded-md bg-neutral-200 dark:bg-neutral-700 text-xs" {...props}>{children}</code>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
        
        {message.context && (
          <div className="mt-1.5 flex items-center gap-1.5 text-[10px] text-neutral-500">
            <Database className="w-3 h-3" />
            <span>From {message.context.sources?.length || 0} sources</span>
          </div>
        )}
      </div>
    </AnimateIn>
  );
};

// ============================================================================
// LOADING INDICATOR
// ============================================================================
const LoadingIndicator = () => (
  <div className="flex gap-3">
    <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center animate-pulse">
      <Bot className="w-4 h-4 text-white" />
    </div>
    <div className="flex-1 max-w-2xl">
      <div className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 mb-1">Allma AI</div>
      <div className="bg-neutral-100 dark:bg-neutral-800 rounded-2xl rounded-tl-sm px-4 py-3 inline-flex items-center gap-2">
        <div className="flex gap-1">
          {[0, 1, 2].map((i) => (
            <span key={i} className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: `${i * 150}ms` }} />
          ))}
        </div>
        <span className="text-xs text-neutral-500">Thinking...</span>
      </div>
    </div>
  </div>
);

// ============================================================================
// EMPTY STATE
// ============================================================================
const EmptyState = ({ onNewChat }) => {
  const features = [
    { icon: MessageSquare, title: 'Natural Chat', desc: 'Conversational AI', color: 'from-violet-500 to-indigo-600' },
    { icon: Database, title: 'RAG Powered', desc: 'Document retrieval', color: 'from-emerald-400 to-cyan-500' },
    { icon: Zap, title: 'Fast & Local', desc: 'Ollama models', color: 'from-amber-400 to-orange-500' },
    { icon: Shield, title: 'Private', desc: 'Data stays local', color: 'from-pink-500 to-rose-500' },
  ];
  
  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full text-center space-y-8">
        <AnimateIn>
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-indigo-600 shadow-xl shadow-violet-500/30 mb-4">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-violet-600 via-indigo-600 to-cyan-500 bg-clip-text text-transparent mb-3">
            Welcome to Allma
          </h1>
          <p className="text-neutral-600 dark:text-neutral-400 max-w-md mx-auto">
            Your intelligent AI assistant powered by local LLMs and RAG
          </p>
        </AnimateIn>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {features.map((f, i) => (
            <AnimateIn key={i} delay={100 + i * 75}>
              <Card hover className="text-center py-4">
                <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} shadow-lg mb-2`}>
                  <f.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-neutral-900 dark:text-white text-sm">{f.title}</h3>
                <p className="text-xs text-neutral-500">{f.desc}</p>
              </Card>
            </AnimateIn>
          ))}
        </div>
        
        <AnimateIn delay={400}>
          <Button size="lg" onClick={onNewChat}>
            <MessageSquare className="w-5 h-5" />
            Start Chatting
          </Button>
        </AnimateIn>
      </div>
    </div>
  );
};

// ============================================================================
// INPUT AREA
// ============================================================================
const InputArea = ({ onSend, isLoading }) => {
  const [message, setMessage] = useState('');
  const textareaRef = useRef(null);
  
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px';
    }
  }, [message]);
  
  const handleSubmit = (e) => {
    e?.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim());
      setMessage('');
    }
  };
  
  return (
    <div className="p-4 md:p-5 bg-gradient-to-t from-neutral-50 dark:from-neutral-950 via-transparent to-transparent">
      <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
        <div className="relative bg-white/90 dark:bg-neutral-900/90 backdrop-blur-xl rounded-2xl border border-neutral-200 dark:border-neutral-700 shadow-lg transition-all focus-within:ring-2 focus-within:ring-violet-500/40 focus-within:border-violet-500/50">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSubmit())}
            placeholder="Ask me anything..."
            disabled={isLoading}
            rows={1}
            className="w-full bg-transparent px-4 py-3.5 pr-14 text-neutral-900 dark:text-white placeholder-neutral-400 resize-none outline-none text-sm"
            style={{ maxHeight: '120px' }}
          />
          <Button type="submit" variant="primary" size="icon" disabled={!message.trim() || isLoading} className="absolute right-2 bottom-2">
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
        <p className="text-[10px] text-neutral-400 text-center mt-1.5">Enter to send • Shift+Enter for new line</p>
      </form>
    </div>
  );
};

// ============================================================================
// SIDEBAR
// ============================================================================
const Sidebar = ({ conversations, activeId, onSelect, onNew, onDelete, darkMode, toggleDarkMode, page, setPage, isOpen, onClose }) => {
  const navItems = [
    { id: 'chat', icon: MessageSquare, label: 'Chats' },
    { id: 'documents', icon: FileText, label: 'Documents' },
    { id: 'settings', icon: Settings, label: 'Settings' },
  ];
  
  return (
    <>
      {isOpen && <div className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={onClose} />}
      
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white/95 dark:bg-neutral-950/95 backdrop-blur-xl border-r border-neutral-200 dark:border-neutral-800 flex flex-col transition-transform duration-300 ${
        isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        {/* Logo */}
        <div className="p-4 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-violet-500/30">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">Allma</h1>
              <p className="text-[10px] text-neutral-500 -mt-0.5">AI Studio</p>
            </div>
          </div>
        </div>
        
        {/* New Chat */}
        <div className="p-3">
          <Button className="w-full" onClick={() => { onNew(); onClose?.(); }}>
            <Plus className="w-4 h-4" /> New Chat
          </Button>
        </div>
        
        {/* Navigation */}
        <nav className="px-2 mb-3">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => { setPage(item.id); onClose?.(); }}
              className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-sm font-medium transition-all ${
                page === item.id
                  ? 'bg-violet-50 dark:bg-violet-900/20 text-violet-600 dark:text-violet-400'
                  : 'text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-800'
              }`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </button>
          ))}
        </nav>
        
        {/* Conversations */}
        {page === 'chat' && (
          <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
            <p className="px-3 py-1.5 text-[10px] font-semibold text-neutral-400 uppercase tracking-wide">Recent</p>
            {conversations.map((conv) => (
              <button
                key={conv.id}
                onClick={() => { onSelect(conv.id); onClose?.(); }}
                className={`w-full group relative flex items-start gap-2 p-2.5 rounded-xl text-left transition-all ${
                  activeId === conv.id
                    ? 'bg-violet-50 dark:bg-violet-900/20 border border-violet-200 dark:border-violet-800/50'
                    : 'hover:bg-neutral-100 dark:hover:bg-neutral-800 border border-transparent'
                }`}
              >
                <MessageSquare className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${activeId === conv.id ? 'text-violet-500' : 'text-neutral-400'}`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-xs font-medium truncate ${activeId === conv.id ? 'text-violet-700 dark:text-violet-300' : 'text-neutral-700 dark:text-neutral-300'}`}>
                    {conv.title}
                  </p>
                  <p className="text-[10px] text-neutral-500 truncate">{conv.preview}</p>
                </div>
                <button
                  onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
                  className="absolute right-1.5 top-1.5 p-1 rounded-lg opacity-0 group-hover:opacity-100 hover:bg-red-100 dark:hover:bg-red-900/30 transition-all"
                >
                  <Trash2 className="w-3 h-3 text-red-500" />
                </button>
              </button>
            ))}
          </div>
        )}
        
        {/* Footer */}
        <div className="p-3 border-t border-neutral-200 dark:border-neutral-800">
          <Button variant="ghost" className="w-full justify-start" onClick={toggleDarkMode}>
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {darkMode ? 'Light Mode' : 'Dark Mode'}
          </Button>
        </div>
      </aside>
    </>
  );
};

// ============================================================================
// DOCUMENTS PAGE
// ============================================================================
const DocumentsPage = ({ settings }) => {
  const [documents, setDocuments] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);
  
  const handleUpload = async (files) => {
    if (!files?.length) return;
    setUploading(true);
    
    for (const file of Array.from(files)) {
      try {
        const formData = new FormData();
        formData.append('file', file);
        await fetch(`${settings.apiUrl}/rag/ingest`, { method: 'POST', body: formData });
        setDocuments((prev) => [...prev, { id: Date.now() + Math.random(), name: file.name, size: file.size, date: new Date() }]);
      } catch (err) {
        console.error('Upload error:', err);
      }
    }
    setUploading(false);
  };
  
  const handleDrag = (e) => {
    e.preventDefault();
    setDragActive(e.type === 'dragenter' || e.type === 'dragover');
  };
  
  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleUpload(e.dataTransfer.files);
  };
  
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6 space-y-5">
        <AnimateIn>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-neutral-900 dark:text-white">Documents</h1>
              <p className="text-sm text-neutral-500">Upload documents for RAG knowledge base</p>
            </div>
            <Badge variant="primary">{documents.length} files</Badge>
          </div>
        </AnimateIn>
        
        <AnimateIn delay={100}>
          <Card 
            className={`border-2 border-dashed text-center py-10 transition-colors ${dragActive ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/10' : 'border-neutral-300 dark:border-neutral-700'}`}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
          >
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-violet-100 dark:bg-violet-900/30 mb-4">
              <Upload className={`w-7 h-7 text-violet-500 ${uploading ? 'animate-bounce' : ''}`} />
            </div>
            <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
              {uploading ? 'Uploading...' : 'Drop files here'}
            </h3>
            <p className="text-sm text-neutral-500 mb-4">or click to browse</p>
            <Button variant="secondary" onClick={() => fileInputRef.current?.click()} disabled={uploading}>
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Select Files'}
            </Button>
            <p className="text-xs text-neutral-400 mt-4">Supports: TXT, PDF, MD, DOC, DOCX</p>
            <input ref={fileInputRef} type="file" multiple accept=".txt,.pdf,.md,.doc,.docx" onChange={(e) => handleUpload(e.target.files)} className="hidden" />
          </Card>
        </AnimateIn>
        
        {documents.length > 0 && (
          <AnimateIn delay={200}>
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-neutral-900 dark:text-white">Uploaded Documents</h3>
                <Button variant="ghost" size="sm" onClick={() => setDocuments([])}>Clear All</Button>
              </div>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div key={doc.id} className="flex items-center gap-3 p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 group">
                    <div className="w-9 h-9 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-violet-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">{doc.name}</p>
                      <p className="text-xs text-neutral-500">{(doc.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <Badge variant="success">Indexed</Badge>
                    <Button variant="ghost" size="icon" onClick={() => setDocuments((d) => d.filter((x) => x.id !== doc.id))} className="opacity-0 group-hover:opacity-100">
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          </AnimateIn>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// SETTINGS PAGE
// ============================================================================
const SettingsPage = ({ settings, setSettings }) => {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto p-6 space-y-5">
        <AnimateIn>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-white">Settings</h1>
          <p className="text-sm text-neutral-500">Configure your AI assistant</p>
        </AnimateIn>
        
        {/* Model Settings */}
        <AnimateIn delay={100}>
          <Card>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900 dark:text-white">Model</h3>
                <p className="text-xs text-neutral-500">Choose your language model</p>
              </div>
            </div>
            
            <div className="grid gap-2">
              {models.map((m) => (
                <label
                  key={m.value}
                  className={`flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all ${
                    settings.model === m.value
                      ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/20'
                      : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600'
                  }`}
                >
                  <input
                    type="radio"
                    name="model"
                    value={m.value}
                    checked={settings.model === m.value}
                    onChange={(e) => setSettings({ ...settings, model: e.target.value })}
                    className="w-4 h-4 text-violet-600 border-neutral-300 focus:ring-violet-500"
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">{m.label}</p>
                    <p className="text-xs text-neutral-500">{m.desc}</p>
                  </div>
                  <Badge>{m.size}</Badge>
                </label>
              ))}
            </div>
          </Card>
        </AnimateIn>
        
        {/* RAG Settings */}
        <AnimateIn delay={200}>
          <Card>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 flex items-center justify-center">
                <Database className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900 dark:text-white">RAG</h3>
                <p className="text-xs text-neutral-500">Document retrieval settings</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <label className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">Enable RAG</p>
                  <p className="text-xs text-neutral-500">Use document context in responses</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, useRAG: !settings.useRAG })}
                  className={`relative w-11 h-6 rounded-full transition-colors ${settings.useRAG ? 'bg-violet-500' : 'bg-neutral-300 dark:bg-neutral-600'}`}
                >
                  <span className={`absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform ${settings.useRAG ? 'translate-x-5' : ''}`} />
                </button>
              </label>
              
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">Documents to Retrieve</p>
                  <Badge variant="primary">{settings.topK}</Badge>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={settings.topK}
                  onChange={(e) => setSettings({ ...settings, topK: parseInt(e.target.value) })}
                  className="w-full h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full appearance-none cursor-pointer accent-violet-500"
                />
              </div>
            </div>
          </Card>
        </AnimateIn>
        
        {/* API Settings */}
        <AnimateIn delay={300}>
          <Card>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                <ExternalLink className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900 dark:text-white">API</h3>
                <p className="text-xs text-neutral-500">Backend connection</p>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">Backend URL</label>
              <input
                type="url"
                value={settings.apiUrl}
                onChange={(e) => setSettings({ ...settings, apiUrl: e.target.value })}
                className="w-full px-3 py-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500 outline-none text-sm"
              />
            </div>
          </Card>
        </AnimateIn>
      </div>
    </div>
  );
};

// ============================================================================
// MAIN APP
// ============================================================================
function App() {
  const [darkMode, toggleDarkMode] = useDarkMode();
  const [conversations, setConversations] = useLocalStorage('conversations', [
    { id: '1', title: 'Welcome', preview: 'Start chatting...', messages: [] },
  ]);
  const [activeId, setActiveId] = useLocalStorage('activeConversationId', '1');
  const [settings, setSettings] = useLocalStorage('settings', defaultSettings);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [page, setPage] = useState('chat');
  const messagesEndRef = useRef(null);
  
  const activeConversation = conversations.find((c) => c.id === activeId);
  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConversation?.messages]);
  
  const handleNewConversation = useCallback(() => {
    const newConv = { id: Date.now().toString(), title: 'New Chat', preview: 'Start chatting...', messages: [] };
    setConversations([newConv, ...conversations]);
    setActiveId(newConv.id);
    setPage('chat');
    setSidebarOpen(false);
  }, [conversations, setConversations, setActiveId]);
  
  const handleDeleteConversation = useCallback((id) => {
    const filtered = conversations.filter((c) => c.id !== id);
    setConversations(filtered.length ? filtered : [{ id: '1', title: 'New Chat', preview: 'Start chatting...', messages: [] }]);
    if (activeId === id) setActiveId(filtered[0]?.id || '1');
  }, [conversations, activeId, setConversations, setActiveId]);
  
  const handleSendMessage = useCallback(async (text) => {
    const userMessage = { role: 'user', content: text, timestamp: Date.now() };
    
    setConversations((convs) =>
      convs.map((c) =>
        c.id === activeId
          ? { ...c, messages: [...c.messages, userMessage], title: c.messages.length === 0 ? text.slice(0, 35) + '...' : c.title, preview: text.slice(0, 50) }
          : c
      )
    );
    
    setIsLoading(true);
    
    try {
      const res = await fetch(`${settings.apiUrl}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, conversation_id: activeId, use_rag: settings.useRAG, model: settings.model }),
      });
      
      const data = res.ok ? await res.json() : null;
      const aiMessage = {
        role: 'assistant',
        content: data?.content || data?.response || '⚠️ Could not get response. Make sure the backend is running.',
        timestamp: Date.now(),
        sources: data?.sources,
      };
      
      setConversations((convs) => convs.map((c) => (c.id === activeId ? { ...c, messages: [...c.messages, aiMessage] } : c)));
    } catch (err) {
      const errorMessage = { role: 'assistant', content: `⚠️ Connection error. Ensure backend is running at ${settings.apiUrl}`, timestamp: Date.now() };
      setConversations((convs) => convs.map((c) => (c.id === activeId ? { ...c, messages: [...c.messages, errorMessage] } : c)));
    } finally {
      setIsLoading(false);
    }
  }, [activeId, settings, setConversations]);
  
  return (
    <div className="h-screen w-screen flex bg-gradient-to-br from-neutral-50 via-white to-violet-50/30 dark:from-neutral-950 dark:via-neutral-900 dark:to-violet-950/20 overflow-hidden">
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onNew={handleNewConversation}
        onDelete={handleDeleteConversation}
        darkMode={darkMode}
        toggleDarkMode={toggleDarkMode}
        page={page}
        setPage={setPage}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />
      
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-14 shrink-0 flex items-center justify-between px-4 border-b border-neutral-200/80 dark:border-neutral-800 bg-white/60 dark:bg-neutral-900/60 backdrop-blur-xl">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </Button>
            <div>
              <h2 className="font-semibold text-neutral-900 dark:text-white text-sm">
                {page === 'chat' ? activeConversation?.title || 'Chat' : page === 'documents' ? 'Documents' : 'Settings'}
              </h2>
              {page === 'chat' && <p className="text-[10px] text-neutral-500">{activeConversation?.messages.length || 0} messages</p>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden sm:flex items-center gap-1.5 text-[10px] text-neutral-500 px-2.5 py-1 rounded-full bg-neutral-100 dark:bg-neutral-800">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Online
            </span>
          </div>
        </header>
        
        {/* Content */}
        {page === 'chat' ? (
          <>
            {activeConversation?.messages.length === 0 ? (
              <EmptyState onNewChat={handleNewConversation} />
            ) : (
              <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
                <div className="max-w-3xl mx-auto space-y-4">
                  {activeConversation?.messages.map((msg, i) => <ChatMessage key={i} message={msg} index={i} />)}
                  {isLoading && <LoadingIndicator />}
                  <div ref={messagesEndRef} />
                </div>
              </div>
            )}
            <InputArea onSend={handleSendMessage} isLoading={isLoading} />
          </>
        ) : page === 'documents' ? (
          <DocumentsPage settings={settings} />
        ) : (
          <SettingsPage settings={settings} setSettings={setSettings} />
        )}
      </div>
      
      {/* Background */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute -top-32 -right-32 w-64 h-64 bg-violet-400/15 rounded-full blur-3xl" />
        <div className="absolute -bottom-32 -left-32 w-64 h-64 bg-cyan-400/15 rounded-full blur-3xl" />
      </div>
    </div>
  );
}

export default App;