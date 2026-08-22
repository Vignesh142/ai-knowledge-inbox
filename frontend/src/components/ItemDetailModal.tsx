import React, { useState, useEffect } from 'react';
import {
  X,
  Globe,
  FileText,
  ExternalLink,
  Layers,
  Sparkles,
  Trash2,
  Copy,
  Check,
  Loader2,
  Calendar,
  User,
  Hash,
  Eye,
  Code2,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Item, ItemDetail } from '../types';
import { getItemDetail } from '../services/api';

interface ItemDetailModalProps {
  item: Item | null;
  onClose: () => void;
  onDelete: (id: string) => void;
  onAskAboutItem: (item: Item) => void;
}

export const ItemDetailModal: React.FC<ItemDetailModalProps> = ({
  item,
  onClose,
  onDelete,
  onAskAboutItem,
}) => {
  const [detail, setDetail] = useState<ItemDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'parsed' | 'chunks' | 'raw'>('parsed');

  useEffect(() => {
    if (item) {
      setLoading(true);
      getItemDetail(item.id)
        .then((res) => {
          setDetail(res);
        })
        .catch((err) => console.error('Failed to load item detail:', err))
        .finally(() => setLoading(false));
    } else {
      setDetail(null);
    }
  }, [item]);

  if (!item) return null;

  const handleCopy = () => {
    if (detail?.content) {
      navigator.clipboard.writeText(detail.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formattedDate = new Date(item.created_at).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  const contentToDisplay = detail?.content || item.content_preview;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4 sm:p-6">
      <div className="flex max-h-[90vh] w-full max-w-3xl flex-col rounded-2xl border border-neutral-200 bg-white shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-start justify-between border-b border-neutral-100 p-5 bg-neutral-50/50">
          <div className="space-y-2 max-w-[85%]">
            <div className="flex flex-wrap items-center gap-2">
              {item.type === 'url' ? (
                <span className="flex items-center gap-1.5 rounded-md bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-100">
                  <Globe className="h-3.5 w-3.5" />
                  <span>Web Page</span>
                </span>
              ) : (
                <span className="flex items-center gap-1.5 rounded-md bg-neutral-100 px-2.5 py-0.5 text-xs font-semibold text-neutral-700 border border-neutral-200">
                  <FileText className="h-3.5 w-3.5" />
                  <span>Note</span>
                </span>
              )}

              {item.url && (
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 text-xs font-medium text-neutral-600 hover:text-neutral-900 bg-white px-2.5 py-0.5 rounded-md border border-neutral-200 shadow-2xs truncate max-w-[280px]"
                >
                  <span className="truncate">{item.source_metadata?.domain || item.url}</span>
                  <ExternalLink className="h-3 w-3 shrink-0" />
                </a>
              )}

              {item.source_metadata?.author && (
                <span className="flex items-center gap-1 text-xs text-neutral-500 bg-neutral-100 px-2 py-0.5 rounded-md">
                  <User className="h-3 w-3" />
                  <span>{item.source_metadata.author}</span>
                </span>
              )}
            </div>

            <h2 className="text-lg font-bold text-neutral-900 leading-snug">{item.title}</h2>

            {/* Tags and Metadata Footer */}
            <div className="flex flex-wrap items-center gap-2 pt-0.5 text-xs text-neutral-400">
              <span className="flex items-center gap-1">
                <Calendar className="h-3.5 w-3.5" />
                <span>{formattedDate}</span>
              </span>
              <span>•</span>
              <span className="flex items-center gap-1 font-medium text-neutral-600">
                <Layers className="h-3.5 w-3.5" />
                <span>{item.chunk_count} {item.chunk_count === 1 ? 'Chunk' : 'Chunks'}</span>
              </span>
              {item.source_metadata?.word_count && (
                <>
                  <span>•</span>
                  <span>{item.source_metadata.word_count} words</span>
                </>
              )}
              {item.tags.map((t) => (
                <span key={t} className="rounded-md bg-neutral-100 px-2 py-0.5 font-medium text-neutral-700 text-[11px] flex items-center gap-0.5">
                  <Hash className="h-2.5 w-2.5 text-neutral-400" />
                  {t}
                </span>
              ))}
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-200 hover:text-neutral-900 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tab switcher */}
        <div className="flex border-b border-neutral-200 bg-white px-5 text-xs font-medium text-neutral-500">
          <button
            onClick={() => setActiveTab('parsed')}
            className={`flex items-center gap-1.5 border-b-2 py-2.5 px-3 transition-colors ${
              activeTab === 'parsed'
                ? 'border-neutral-900 text-neutral-900 font-semibold'
                : 'border-transparent hover:text-neutral-900'
            }`}
          >
            <Eye className="h-3.5 w-3.5" />
            <span>Parsed Content</span>
          </button>
          <button
            onClick={() => setActiveTab('chunks')}
            className={`flex items-center gap-1.5 border-b-2 py-2.5 px-3 transition-colors ${
              activeTab === 'chunks'
                ? 'border-neutral-900 text-neutral-900 font-semibold'
                : 'border-transparent hover:text-neutral-900'
            }`}
          >
            <Layers className="h-3.5 w-3.5" />
            <span>Vector Chunks ({detail?.chunks?.length || item.chunk_count})</span>
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`flex items-center gap-1.5 border-b-2 py-2.5 px-3 transition-colors ${
              activeTab === 'raw'
                ? 'border-neutral-900 text-neutral-900 font-semibold'
                : 'border-transparent hover:text-neutral-900'
            }`}
          >
            <Code2 className="h-3.5 w-3.5" />
            <span>Raw Text</span>
          </button>
        </div>

        {/* Body content */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center py-16 text-xs text-neutral-500">
              <Loader2 className="h-5 w-5 animate-spin mr-2 text-neutral-900" />
              <span>Loading document and chunk embeddings...</span>
            </div>
          ) : activeTab === 'parsed' ? (
            <div className="space-y-4">
              {/* URL Preview Card if applicable */}
              {item.type === 'url' && item.source_metadata?.description && (
                <div className="rounded-xl border border-neutral-200 bg-neutral-50/70 p-4 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-semibold text-neutral-500 uppercase tracking-wider">
                      Website Metadata Summary
                    </span>
                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-neutral-900 font-medium underline flex items-center gap-1"
                      >
                        Visit original website <ExternalLink className="h-3 w-3" />
                      </a>
                    )}
                  </div>
                  <p className="text-xs text-neutral-700 leading-relaxed font-medium">
                    {item.source_metadata.description}
                  </p>
                </div>
              )}

              {/* Formatted Markdown Body */}
              <div className="markdown-body text-xs sm:text-sm leading-relaxed text-neutral-800 bg-white">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {contentToDisplay}
                </ReactMarkdown>
              </div>
            </div>
          ) : activeTab === 'chunks' ? (
            <div className="space-y-3">
              <p className="text-xs text-neutral-500">
                This document was partitioned using recursive character boundary splitting. Each chunk is individually embedded into the ChromaDB vector store.
              </p>
              <div className="space-y-3">
                {detail?.chunks?.map((chunk, idx) => (
                  <div
                    key={chunk.id}
                    className="rounded-xl border border-neutral-200 bg-neutral-50/70 p-4 text-xs shadow-2xs hover:border-neutral-300 hover:bg-white transition-all"
                  >
                    <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-neutral-200 text-[11px] text-neutral-500">
                      <span className="font-semibold text-neutral-800 flex items-center gap-1.5">
                        <span className="flex h-4.5 w-4.5 items-center justify-center rounded-full bg-neutral-900 text-white text-[10px]">
                          {idx + 1}
                        </span>
                        <span>Chunk #{chunk.chunk_index + 1}</span>
                      </span>
                      <div className="flex items-center gap-2">
                        <span>{chunk.char_count} chars</span>
                        <span>•</span>
                        <span>~{chunk.token_estimate} tokens</span>
                      </div>
                    </div>
                    <div className="markdown-body text-xs leading-relaxed text-neutral-700 bg-white p-3 rounded-lg border border-neutral-100 font-mono text-[11px]">
                      {chunk.text}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="rounded-xl border border-neutral-200 bg-neutral-900 text-neutral-100 p-4 font-mono text-xs whitespace-pre-wrap leading-relaxed overflow-x-auto">
                {contentToDisplay}
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex items-center justify-between border-t border-neutral-100 bg-neutral-50/50 p-4">
          <button
            onClick={() => {
              if (confirm(`Delete "${item.title}"?`)) {
                onDelete(item.id);
                onClose();
              }
            }}
            className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            <span>Delete Item</span>
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-xs font-medium text-neutral-700 shadow-2xs hover:bg-neutral-50 transition-all"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
              <span>{copied ? 'Copied' : 'Copy Content'}</span>
            </button>
            <button
              onClick={() => {
                onAskAboutItem(item);
                onClose();
              }}
              className="flex items-center gap-1.5 rounded-lg bg-neutral-900 px-4 py-1.5 text-xs font-medium text-white shadow-xs hover:bg-neutral-800 transition-all"
            >
              <Sparkles className="h-3.5 w-3.5" />
              <span>Query With AI</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
