/**
 * SettingsPage Component
 * 
 * Application settings interface.
 */

import React, { useState, useEffect } from 'react';
import { Zap, Database, ExternalLink, RefreshCw, Check, AlertCircle } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import Badge from '../ui/Badge';
import AnimateIn from '../ui/AnimateIn';
import { useModels, useHealthCheck } from '../../hooks';
import api from '../../services/api';

const AVAILABLE_MODELS = [
  { value: 'deepseek-r1:latest', label: 'DeepSeek R1', size: '5.2GB', desc: 'Best for reasoning' },
  { value: 'gemma2:9b', label: 'Gemma 2 9B', size: '5.4GB', desc: 'Balanced performance' },
  { value: 'qwen2.5-coder:7b', label: 'Qwen 2.5 Coder', size: '4.7GB', desc: 'Optimized for code' },
  { value: 'llama3.2:latest', label: 'Llama 3.2', size: '2.0GB', desc: 'Fast and efficient' },
];

const SettingsPage = ({ settings, setSettings }) => {
  const { status, refresh: refreshHealth } = useHealthCheck(60000);
  const { models, currentModel, fetchModels, switchModel, isLoading: modelsLoading } = useModels();
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);

  // Update API URL when settings change
  useEffect(() => {
    if (settings?.apiUrl) {
      api.setBaseUrl(settings.apiUrl);
    }
  }, [settings?.apiUrl]);

  const testConnection = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await api.healthCheck();
      setTestResult({ success: true, message: `Connected! Status: ${result.status}` });
    } catch (err) {
      setTestResult({ success: false, message: err.message });
    }
    setTesting(false);
  };

  const handleModelChange = async (modelValue) => {
    setSettings({ ...settings, model: modelValue });
    try {
      await switchModel(modelValue);
    } catch (err) {
      console.error('Failed to switch model:', err);
    }
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto p-6 space-y-5">
        {/* Header */}
        <AnimateIn>
          <h1 className="text-xl font-bold text-neutral-900 dark:text-white">
            Settings
          </h1>
          <p className="text-sm text-neutral-500">Configure your AI assistant</p>
        </AnimateIn>

        {/* Model Settings */}
        <AnimateIn delay={100}>
          <Card>
            <div className="flex items-center gap-3 mb-5">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-neutral-900 dark:text-white">
                  Model
                </h3>
                <p className="text-xs text-neutral-500">Choose your language model</p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchModels}
                loading={modelsLoading}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>

            <div className="grid gap-2">
              {AVAILABLE_MODELS.map((m) => (
                <label
                  key={m.value}
                  className={`
                    flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all
                    ${settings.model === m.value
                      ? 'border-violet-500 bg-violet-50 dark:bg-violet-900/20'
                      : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300 dark:hover:border-neutral-600'
                    }
                  `}
                >
                  <input
                    type="radio"
                    name="model"
                    value={m.value}
                    checked={settings.model === m.value}
                    onChange={(e) => handleModelChange(e.target.value)}
                    className="w-4 h-4 text-violet-600 border-neutral-300 focus:ring-violet-500"
                  />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">
                      {m.label}
                    </p>
                    <p className="text-xs text-neutral-500">{m.desc}</p>
                  </div>
                  <Badge>{m.size}</Badge>
                </label>
              ))}
            </div>

            {/* Available models from server */}
            {models.length > 0 && (
              <div className="mt-4 pt-4 border-t border-neutral-200 dark:border-neutral-700">
                <p className="text-xs font-medium text-neutral-500 mb-2">
                  Available on server:
                </p>
                <div className="flex flex-wrap gap-1">
                  {models.map((m) => (
                    <Badge key={m.name} variant="default" size="xs">
                      {m.name}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
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
                <h3 className="font-semibold text-neutral-900 dark:text-white">
                  RAG
                </h3>
                <p className="text-xs text-neutral-500">Document retrieval settings</p>
              </div>
            </div>

            <div className="space-y-4">
              {/* RAG Toggle */}
              <label className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    Enable RAG
                  </p>
                  <p className="text-xs text-neutral-500">
                    Use document context in responses
                  </p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, useRAG: !settings.useRAG })}
                  className={`
                    relative w-11 h-6 rounded-full transition-colors
                    ${settings.useRAG ? 'bg-violet-500' : 'bg-neutral-300 dark:bg-neutral-600'}
                  `}
                >
                  <span
                    className={`
                      absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow transition-transform
                      ${settings.useRAG ? 'translate-x-5' : ''}
                    `}
                  />
                </button>
              </label>

              {/* Top K Slider */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">
                    Documents to Retrieve
                  </p>
                  <Badge variant="primary">{settings.topK}</Badge>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={settings.topK}
                  onChange={(e) =>
                    setSettings({ ...settings, topK: parseInt(e.target.value) })
                  }
                  className="w-full h-2 bg-neutral-200 dark:bg-neutral-700 rounded-full appearance-none cursor-pointer accent-violet-500"
                />
                <div className="flex justify-between mt-1 text-[10px] text-neutral-400">
                  <span>1</span>
                  <span>5</span>
                  <span>10</span>
                </div>
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
              <div className="flex-1">
                <h3 className="font-semibold text-neutral-900 dark:text-white">
                  API Connection
                </h3>
                <p className="text-xs text-neutral-500">Backend connection settings</p>
              </div>
              <Badge
                variant={status === 'healthy' ? 'success' : status === 'degraded' ? 'warning' : 'error'}
              >
                {status}
              </Badge>
            </div>

            <div className="space-y-4">
              {/* API URL Input */}
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
                  Backend URL
                </label>
                <input
                  type="url"
                  value={settings.apiUrl}
                  onChange={(e) =>
                    setSettings({ ...settings, apiUrl: e.target.value })
                  }
                  className="w-full px-3 py-2.5 rounded-xl bg-neutral-50 dark:bg-neutral-800 border border-neutral-200 dark:border-neutral-700 focus:ring-2 focus:ring-violet-500/40 focus:border-violet-500 outline-none text-sm"
                  placeholder="http://localhost:8000"
                />
              </div>

              {/* Test Connection */}
              <div className="flex items-center gap-3">
                <Button
                  variant="secondary"
                  onClick={testConnection}
                  loading={testing}
                >
                  Test Connection
                </Button>
                <Button variant="ghost" onClick={refreshHealth}>
                  <RefreshCw className="w-4 h-4" />
                  Refresh Status
                </Button>
              </div>

              {/* Test Result */}
              {testResult && (
                <div
                  className={`
                    flex items-center gap-2 p-3 rounded-xl text-sm
                    ${testResult.success
                      ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400'
                      : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                    }
                  `}
                >
                  {testResult.success ? (
                    <Check className="w-4 h-4" />
                  ) : (
                    <AlertCircle className="w-4 h-4" />
                  )}
                  {testResult.message}
                </div>
              )}
            </div>
          </Card>
        </AnimateIn>

        {/* About */}
        <AnimateIn delay={400}>
          <Card className="text-center">
            <p className="text-xs text-neutral-500">
              Allma AI Studio v2.0.0
            </p>
            <p className="text-xs text-neutral-400 mt-1">
              Powered by Ollama • Built with React + FastAPI
            </p>
          </Card>
        </AnimateIn>
      </div>
    </div>
  );
};

export default SettingsPage;
