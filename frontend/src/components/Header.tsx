import React from 'react';
import { Sparkles, Database, Layers, Info, Plus } from 'lucide-react';
import { Stats } from '../types';

interface HeaderProps {
  stats: Stats | null;
  onOpenStats: () => void;
  onToggleChat: () => void;
  isChatOpen: boolean;
  onFocusIngest: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  stats,
  onOpenStats,
  onToggleChat,
  isChatOpen,
  onFocusIngest,
}) => {
  return (
    <header className="sticky top-0 z-30 border-b border-neutral-200 bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-xs">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-neutral-900">
                AI Knowledge Inbox
              </h1>
              <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-[11px] font-medium text-neutral-600 border border-neutral-200">
                RAG v1.0
              </span>
            </div>
            <p className="hidden text-xs text-neutral-500 sm:block">
              Intelligent notes, server-side URL scraper & semantic search
            </p>
          </div>
        </div>

        {/* Action Controls & Live Stats */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Quick Stat Pill */}
          {stats && (
            <button
              onClick={onOpenStats}
              className="hidden md:flex items-center gap-3 rounded-full border border-neutral-200 bg-neutral-50 px-3 py-1.5 text-xs text-neutral-700 hover:bg-neutral-100 transition-colors"
              title="Click to view Vector DB and RAG Pipeline diagnostics"
            >
              <div className="flex items-center gap-1.5 font-medium">
                <Database className="h-3.5 w-3.5 text-neutral-500" />
                <span>{stats.total_items} items</span>
              </div>
              <div className="h-3 w-[1px] bg-neutral-300" />
              <div className="flex items-center gap-1.5 font-medium">
                <Layers className="h-3.5 w-3.5 text-neutral-500" />
                <span>{stats.total_chunks} chunks</span>
              </div>
              <div className="h-3 w-[1px] bg-neutral-300" />
              <span className="truncate max-w-[120px] text-neutral-500 text-[11px]">
                {stats.active_llm_provider.split(' ')[0]}
              </span>
            </button>
          )}

          {/* New Item Button */}
          <button
            onClick={onFocusIngest}
            className="flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-xs font-medium text-neutral-700 shadow-xs hover:bg-neutral-50 active:bg-neutral-100 transition-all"
          >
            <Plus className="h-4 w-4" />
            <span className="hidden sm:inline">Add Item</span>
          </button>

          {/* System Diagnostics Info */}
          <button
            onClick={onOpenStats}
            className="rounded-lg p-2 text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 transition-colors"
            title="System Architecture & Vector DB Stats"
          >
            <Info className="h-4 w-4" />
          </button>

          {/* AI Query Assistant Toggle */}
          <button
            onClick={onToggleChat}
            className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-medium transition-all shadow-xs ${
              isChatOpen
                ? 'bg-neutral-900 text-white hover:bg-neutral-800'
                : 'bg-neutral-100 text-neutral-900 hover:bg-neutral-200 border border-neutral-300'
            }`}
          >
            <Sparkles className="h-4 w-4" />
            <span>AI Query Assistant</span>
            <kbd className="hidden lg:inline-block rounded bg-white/20 px-1.5 py-0.5 text-[10px] font-mono">
              Ctrl+K
            </kbd>
          </button>
        </div>
      </div>
    </header>
  );
};
