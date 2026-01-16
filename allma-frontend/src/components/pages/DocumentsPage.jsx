/**
 * DocumentsPage Component
 * 
 * Document upload and management interface.
 */

import React, { useState, useRef } from 'react';
import { Upload, FileText, Trash2, Loader2, Search, FolderOpen } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import AnimateIn from '../ui/AnimateIn';
import { useDocuments, useSearch } from '../../hooks';
import api from '../../services/api';

const DocumentsPage = ({ settings }) => {
  const {
    documents,
    isUploading,
    uploadDocument,
    deleteDocument,
    clearAll,
  } = useDocuments();
  
  const { results, isSearching, search, clearResults } = useSearch();
  const [dragActive, setDragActive] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const fileInputRef = useRef(null);

  // Configure API URL
  if (settings?.apiUrl) {
    api.setBaseUrl(settings.apiUrl);
  }

  const handleUpload = async (files) => {
    if (!files?.length) return;
    
    for (const file of Array.from(files)) {
      try {
        await uploadDocument(file);
      } catch (err) {
        console.error('Upload error:', err);
      }
    }
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

  const handleSearch = async (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      await search(searchQuery, { topK: settings?.topK || 5 });
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto p-6 space-y-5">
        {/* Header */}
        <AnimateIn>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
                Documents
              </h1>
              <p className="text-sm text-neutral-500">
                Upload documents for RAG knowledge base
              </p>
            </div>
            <Badge variant="primary">{documents.length} files</Badge>
          </div>
        </AnimateIn>

        {/* Upload Zone */}
        <AnimateIn delay={100}>
          <Card
            className={`
              border-2 border-dashed text-center py-10 transition-colors
              ${dragActive
                ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/10'
                : 'border-neutral-300 dark:border-neutral-700'
              }
            `}
            padding={false}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
          >
            <div className="p-6">
              <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-violet-100 dark:bg-violet-900/30 mb-4">
                <Upload
                  className={`w-7 h-7 text-violet-500 ${isUploading ? 'animate-bounce' : ''}`}
                />
              </div>
              <h3 className="font-semibold text-neutral-900 dark:text-white mb-1">
                {isUploading ? 'Uploading...' : 'Drop files here'}
              </h3>
              <p className="text-sm text-neutral-500 mb-4">or click to browse</p>
              <Button
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                loading={isUploading}
              >
                Select Files
              </Button>
              <p className="text-xs text-neutral-400 mt-4">
                Supports: TXT, PDF, MD, DOC, DOCX, HTML, JSON, CSV
              </p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".txt,.pdf,.md,.doc,.docx,.html,.json,.csv"
                onChange={(e) => handleUpload(e.target.files)}
                className="hidden"
              />
            </div>
          </Card>
        </AnimateIn>

        {/* Search */}
        <AnimateIn delay={150}>
          <Card>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center">
                <Search className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900 dark:text-white">
                  Semantic Search
                </h3>
                <p className="text-xs text-neutral-500">
                  Search your knowledge base
                </p>
              </div>
            </div>

            <form onSubmit={handleSearch} className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search documents..."
                className="flex-1 px-3 py-2 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500 outline-none text-sm"
              />
              <Button type="submit" loading={isSearching}>
                <Search className="w-4 h-4" />
                Search
              </Button>
            </form>

            {/* Search Results */}
            {results.length > 0 && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between">
                  <p className="text-xs font-medium text-neutral-500">
                    {results.length} results found
                  </p>
                  <Button variant="ghost" size="sm" onClick={clearResults}>
                    Clear
                  </Button>
                </div>
                {results.map((result, i) => (
                  <div
                    key={i}
                    className="p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 border border-neutral-200 dark:border-neutral-700"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-violet-600 dark:text-violet-400">
                        {result.source}
                      </span>
                      <Badge variant="success" size="xs">
                        {(result.score * 100).toFixed(1)}%
                      </Badge>
                    </div>
                    <p className="text-sm text-neutral-700 dark:text-neutral-300 line-clamp-3">
                      {result.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </AnimateIn>

        {/* Documents List */}
        {documents.length > 0 && (
          <AnimateIn delay={200}>
            <Card>
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-neutral-900 dark:text-white">
                  Uploaded Documents
                </h3>
                <Button variant="ghost" size="sm" onClick={clearAll}>
                  Clear All
                </Button>
              </div>
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center gap-3 p-3 rounded-xl bg-neutral-50 dark:bg-neutral-800/50 group"
                  >
                    <div className="w-9 h-9 rounded-lg bg-violet-100 dark:bg-violet-900/30 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-violet-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-neutral-900 dark:text-white truncate">
                        {doc.name}
                      </p>
                      <p className="text-xs text-neutral-500">
                        {formatFileSize(doc.size)}
                        {doc.chunksCreated && ` • ${doc.chunksCreated} chunks`}
                      </p>
                    </div>
                    <Badge variant="success">Indexed</Badge>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => deleteDocument(doc.id)}
                      className="opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-4 h-4 text-red-500" />
                    </Button>
                  </div>
                ))}
              </div>
            </Card>
          </AnimateIn>
        )}

        {/* Empty State */}
        {documents.length === 0 && (
          <AnimateIn delay={200}>
            <Card className="text-center py-10">
              <FolderOpen className="w-12 h-12 mx-auto text-neutral-300 dark:text-neutral-600 mb-3" />
              <h3 className="font-medium text-neutral-900 dark:text-white mb-1">
                No documents yet
              </h3>
              <p className="text-sm text-neutral-500">
                Upload documents to build your knowledge base
              </p>
            </Card>
          </AnimateIn>
        )}
      </div>
    </div>
  );
};

export default DocumentsPage;
