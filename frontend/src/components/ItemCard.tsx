import React, { useState } from 'react';
import {
  FileText,
  Globe,
  ExternalLink,
  Layers,
  Copy,
  Check,
  Trash2,
  Sparkles,
  Maximize2,
} from 'lucide-react';
import { Item } from '../types';

interface ItemCardProps {
  item: Item;
  onSelect: (item: Item) => void;
  onDelete: (id: string) => void;
  onAskAboutItem: (item: Item) => void;
  onTagClick?: (tag: string) => void;
}

export const ItemCard: React.FC<ItemCardProps> = ({
  item,
  onSelect,
  onDelete,
  onAskAboutItem,
  onTagClick,
}) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(item.content_preview);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm(`Are you sure you want to delete "${item.title}"?`)) {
      setIsDeleting(true);
      onDelete(item.id);
    }
  };

  const formattedDate = new Date(item.created_at).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div
      onClick={() => onSelect(item)}
      className="group relative flex flex-col justify-between rounded-xl border border-neutral-200 bg-white p-4 shadow-2xs hover:border-neutral-400 hover:shadow-xs transition-all cursor-pointer"
    >
      <div>
        {/* Card Header: Type Badge, Title, Actions */}
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-1.5">
            {item.type === 'url' ? (
              <span className="flex items-center gap-1 rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-medium text-blue-700 border border-blue-100">
                <Globe className="h-3 w-3" />
                <span>URL</span>
              </span>
            ) : (
              <span className="flex items-center gap-1 rounded-md bg-neutral-100 px-2 py-0.5 text-[11px] font-medium text-neutral-700 border border-neutral-200">
                <FileText className="h-3 w-3" />
                <span>Note</span>
              </span>
            )}

            {item.url && item.source_metadata?.domain && (
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="flex items-center gap-1 text-[11px] text-neutral-500 hover:text-neutral-900 truncate max-w-[140px]"
                title={item.url}
              >
                <span>{item.source_metadata.domain}</span>
                <ExternalLink className="h-2.5 w-2.5 shrink-0 opacity-70" />
              </a>
            )}
          </div>

          {/* Quick Hover Controls */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAskAboutItem(item);
              }}
              className="rounded p-1 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 transition-colors"
              title="Ask AI about this item"
            >
              <Sparkles className="h-3.5 w-3.5 text-amber-600" />
            </button>
            <button
              onClick={handleCopy}
              className="rounded p-1 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 transition-colors"
              title="Copy snippet"
            >
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-600" /> : <Copy className="h-3.5 w-3.5" />}
            </button>
            <button
              onClick={handleDelete}
              disabled={isDeleting}
              className="rounded p-1 text-neutral-400 hover:bg-red-50 hover:text-red-600 transition-colors"
              title="Delete item"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* Title */}
        <h3 className="mt-2 text-sm font-semibold text-neutral-900 line-clamp-2 leading-snug">
          {item.title}
        </h3>

        {/* Snippet Preview */}
        <p className="mt-1.5 text-xs text-neutral-600 line-clamp-4 leading-relaxed font-normal">
          {item.content_preview}
        </p>

        {/* Tags */}
        {item.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {item.tags.map((tag) => (
              <button
                key={tag}
                onClick={(e) => {
                  e.stopPropagation();
                  onTagClick?.(tag);
                }}
                className="rounded-md bg-neutral-100 px-1.5 py-0.5 text-[10px] font-medium text-neutral-600 hover:bg-neutral-200 transition-colors"
              >
                #{tag}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Card Footer: Metadata info */}
      <div className="mt-4 pt-2.5 border-t border-neutral-100 flex items-center justify-between text-[11px] text-neutral-400">
        <div className="flex items-center gap-2">
          <span className="flex items-center gap-1 font-medium text-neutral-500">
            <Layers className="h-3 w-3" />
            <span>{item.chunk_count} {item.chunk_count === 1 ? 'chunk' : 'chunks'}</span>
          </span>
          {item.source_metadata?.word_count && (
            <>
              <span>•</span>
              <span>{item.source_metadata.word_count} words</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <span>{formattedDate}</span>
          <Maximize2 className="h-3 w-3 opacity-0 group-hover:opacity-60 transition-opacity" />
        </div>
      </div>
    </div>
  );
};
