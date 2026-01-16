/**
 * EmptyState Component
 * 
 * Welcome screen when no messages exist.
 */

import React from 'react';
import { MessageSquare, Database, Zap, Shield, Sparkles } from 'lucide-react';
import Button from '../ui/Button';
import Card from '../ui/Card';
import AnimateIn from '../ui/AnimateIn';

const EmptyState = ({ onNewChat }) => {
  const features = [
    {
      icon: MessageSquare,
      title: 'Natural Chat',
      desc: 'Conversational AI',
      color: 'from-violet-500 to-indigo-600',
    },
    {
      icon: Database,
      title: 'RAG Powered',
      desc: 'Document retrieval',
      color: 'from-emerald-400 to-cyan-500',
    },
    {
      icon: Zap,
      title: 'Fast & Local',
      desc: 'Ollama models',
      color: 'from-amber-400 to-orange-500',
    },
    {
      icon: Shield,
      title: 'Private',
      desc: 'Data stays local',
      color: 'from-pink-500 to-rose-500',
    },
  ];

  const suggestions = [
    'What can you help me with?',
    'Summarize the uploaded documents',
    'Explain this code to me',
    'Help me write a Python script',
  ];

  return (
    <div className="flex-1 flex items-center justify-center p-6">
      <div className="max-w-2xl w-full text-center space-y-8">
        {/* Hero */}
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

        {/* Features */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {features.map((f, i) => (
            <AnimateIn key={i} delay={100 + i * 75}>
              <Card hover className="text-center py-4">
                <div
                  className={`inline-flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br ${f.color} shadow-lg mb-2`}
                >
                  <f.icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-semibold text-neutral-900 dark:text-white text-sm">
                  {f.title}
                </h3>
                <p className="text-xs text-neutral-500">{f.desc}</p>
              </Card>
            </AnimateIn>
          ))}
        </div>

        {/* Suggestions */}
        <AnimateIn delay={350}>
          <div className="space-y-3">
            <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">
              Try asking
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {suggestions.map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => onNewChat?.(suggestion)}
                  className="px-3 py-1.5 text-xs rounded-full bg-neutral-100 dark:bg-neutral-800 text-neutral-600 dark:text-neutral-400 hover:bg-violet-100 dark:hover:bg-violet-900/30 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        </AnimateIn>

        {/* CTA */}
        <AnimateIn delay={400}>
          <Button size="lg" onClick={() => onNewChat?.()}>
            <MessageSquare className="w-5 h-5" />
            Start Chatting
          </Button>
        </AnimateIn>
      </div>
    </div>
  );
};

export default EmptyState;
