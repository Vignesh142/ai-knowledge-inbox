import React from 'react';
import { X, Database, Cpu, Server, Shield, Sparkles } from 'lucide-react';
import type { Stats } from '../types';

interface StatsModalProps {
  stats: Stats | null;
  isOpen: boolean;
  onClose: () => void;
}

export const StatsModal: React.FC<StatsModalProps> = ({ stats, isOpen, onClose }) => {
  if (!isOpen || !stats) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 sm:p-6">
      <div className="flex max-h-[90vh] w-full max-w-2xl flex-col rounded-2xl border border-neutral-200 bg-white shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-neutral-100 p-5 bg-neutral-50/50">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-neutral-900 text-white">
              <Server className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-neutral-900">System Architecture & Diagnostics</h2>
              <p className="text-[11px] text-neutral-500">RAG pipeline, vector database, and adapter status</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-200 hover:text-neutral-900 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Key Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border border-neutral-200 bg-neutral-50/50 p-3.5 text-center">
              <span className="text-2xl font-bold text-neutral-900">{stats.total_items}</span>
              <p className="text-[11px] font-medium text-neutral-500 mt-0.5">Total Items</p>
            </div>
            <div className="rounded-xl border border-neutral-200 bg-neutral-50/50 p-3.5 text-center">
              <span className="text-2xl font-bold text-neutral-900">{stats.total_notes}</span>
              <p className="text-[11px] font-medium text-neutral-500 mt-0.5">Text Notes</p>
            </div>
            <div className="rounded-xl border border-neutral-200 bg-neutral-50/50 p-3.5 text-center">
              <span className="text-2xl font-bold text-neutral-900">{stats.total_urls}</span>
              <p className="text-[11px] font-medium text-neutral-500 mt-0.5">Saved URLs</p>
            </div>
            <div className="rounded-xl border border-neutral-200 bg-neutral-50/50 p-3.5 text-center">
              <span className="text-2xl font-bold text-neutral-900">{stats.total_chunks}</span>
              <p className="text-[11px] font-medium text-neutral-500 mt-0.5">Vector Chunks</p>
            </div>
          </div>

          {/* Active AI Stack */}
          <div className="rounded-xl border border-neutral-200 bg-white p-4 space-y-3 shadow-2xs">
            <h3 className="text-xs font-semibold text-neutral-900 uppercase tracking-wider">
              Active AI Configuration
            </h3>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between py-1.5 border-b border-neutral-100">
                <span className="text-neutral-500 flex items-center gap-1.5">
                  <Cpu className="h-3.5 w-3.5 text-neutral-400" />
                  <span>LLM Synthesis Provider</span>
                </span>
                <span className="font-semibold text-neutral-800">{stats.active_llm_provider}</span>
              </div>

              <div className="flex items-center justify-between py-1.5 border-b border-neutral-100">
                <span className="text-neutral-500 flex items-center gap-1.5">
                  <Sparkles className="h-3.5 w-3.5 text-neutral-400" />
                  <span>Vector Embedding Engine</span>
                </span>
                <span className="font-semibold text-neutral-800">{stats.active_embedding_provider}</span>
              </div>

              <div className="flex items-center justify-between py-1.5">
                <span className="text-neutral-500 flex items-center gap-1.5">
                  <Database className="h-3.5 w-3.5 text-neutral-400" />
                  <span>Vector Store Engine</span>
                </span>
                <span className="font-semibold text-neutral-800">{stats.vector_store_backend}</span>
              </div>
            </div>
          </div>

          {/* Tags in System */}
          {stats.all_tags.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold text-neutral-900 uppercase tracking-wider">
                Indexed Tags ({stats.all_tags.length})
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {stats.all_tags.map((t) => (
                  <span
                    key={t}
                    className="rounded-md bg-neutral-100 px-2.5 py-1 text-xs font-medium text-neutral-700 border border-neutral-200"
                  >
                    #{t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Architecture Badges */}
          <div className="rounded-xl border border-neutral-200 bg-neutral-50/70 p-4 text-xs text-neutral-600 space-y-2">
            <h4 className="font-semibold text-neutral-900 flex items-center gap-1.5">
              <Shield className="h-4 w-4 text-emerald-600" />
              <span>Production Safeguards Enabled</span>
            </h4>
            <ul className="space-y-1 list-disc pl-4 text-[11px] text-neutral-600">
              <li>Server-Side URL Scraper with SSRF protection against private IP & cloud metadata exploits</li>
              <li>Intentional Recursive Chunker preserving semantic sentence and paragraph boundaries</li>
              <li>Server-Sent Events (SSE) streaming for real-time token generation and citation delivery</li>
              <li>Async SQLite with Pydantic serialization & cascade vector deletion</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-neutral-100 bg-neutral-50/50 p-4 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-lg bg-neutral-900 px-4 py-1.5 text-xs font-medium text-white hover:bg-neutral-800 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
