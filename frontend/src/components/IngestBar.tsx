import React, { useState, useRef, useEffect } from 'react';
import { FileText, Globe, Tag, X, ArrowRight, Loader2, CheckCircle2, AlertCircle } from 'lucide-react';
import { ItemType, IngestPayload, Item } from '../types';
import { ingestItem } from '../services/api';

interface IngestBarProps {
  onItemIngested: (item: Item) => void;
  inputRef?: React.RefObject<HTMLTextAreaElement | HTMLInputElement | null>;
}

export const IngestBar: React.FC<IngestBarProps> = ({ onItemIngested, inputRef: externalRef }) => {
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [type, setType] = useState<ItemType>('note');
  const [title, setTitle] = useState<string>('');
  const [content, setContent] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [tagInput, setTagInput] = useState<string>('');
  const [tags, setTags] = useState<string[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<{ text: string; isError: boolean } | null>(null);

  const containerRef = useRef<HTMLDivElement>(null);
  const localNoteInputRef = useRef<HTMLTextAreaElement>(null);
  const localUrlInputRef = useRef<HTMLInputElement>(null);

  // Auto-detect URL when typing or pasting in note mode
  const handleContentChange = (val: string) => {
    setContent(val);
    if (!url && val.trim().startsWith('http://') || val.trim().startsWith('https://')) {
      if (val.trim().split(/\s+/).length === 1) {
        setType('url');
        setUrl(val.trim());
        setContent('');
      }
    }
  };

  const handleAddTag = () => {
    const cleanTag = tagInput.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '');
    if (cleanTag && !tags.includes(cleanTag)) {
      setTags([...tags, cleanTag]);
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setTags(tags.filter((t) => t !== tagToRemove));
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    if (type === 'note' && !content.trim()) {
      setStatusMessage({ text: 'Please enter note content.', isError: true });
      return;
    }
    if (type === 'url' && !url.trim()) {
      setStatusMessage({ text: 'Please enter a valid website URL.', isError: true });
      return;
    }

    setLoading(true);
    setStatusMessage(null);

    const payload: IngestPayload = {
      type,
      title: title.trim() || undefined,
      tags,
      ...(type === 'note' ? { content: content.trim() } : { url: url.trim() }),
    };

    try {
      const newItem = await ingestItem(payload);
      onItemIngested(newItem);
      // Reset form
      setContent('');
      setUrl('');
      setTitle('');
      setTags([]);
      setTagInput('');
      setIsExpanded(false);
      setStatusMessage({
        text: `Successfully ingested "${newItem.title}" into knowledge inbox!`,
        isError: false,
      });
      setTimeout(() => setStatusMessage(null), 4000);
    } catch (err: any) {
      setStatusMessage({
        text: err?.message || 'Failed to ingest item. Please verify and try again.',
        isError: true,
      });
    } finally {
      setLoading(false);
    }
  };

  // Close card when clicking outside if empty
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node) &&
        !content.trim() &&
        !url.trim() &&
        !title.trim()
      ) {
        setIsExpanded(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [content, url, title]);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-4" ref={containerRef}>
      <div
        className={`relative overflow-hidden rounded-xl border bg-white shadow-xs transition-all duration-200 ${
          isExpanded
            ? 'border-neutral-900 shadow-md ring-1 ring-neutral-900/5'
            : 'border-neutral-200 hover:border-neutral-300 hover:shadow-xs'
        }`}
      >
        {/* Type Toggle Tabs (when expanded) */}
        {isExpanded && (
          <div className="flex border-b border-neutral-100 bg-neutral-50/70 px-4 py-2 text-xs font-medium text-neutral-600">
            <div className="flex gap-1.5">
              <button
                type="button"
                onClick={() => setType('note')}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-colors ${
                  type === 'note'
                    ? 'bg-white text-neutral-900 font-semibold shadow-xs border border-neutral-200'
                    : 'text-neutral-500 hover:text-neutral-900'
                }`}
              >
                <FileText className="h-3.5 w-3.5" />
                <span>Text Note</span>
              </button>
              <button
                type="button"
                onClick={() => setType('url')}
                className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-colors ${
                  type === 'url'
                    ? 'bg-white text-neutral-900 font-semibold shadow-xs border border-neutral-200'
                    : 'text-neutral-500 hover:text-neutral-900'
                }`}
              >
                <Globe className="h-3.5 w-3.5" />
                <span>Save Web URL</span>
              </button>
            </div>
          </div>
        )}

        <div className="p-3 sm:p-4">
          {/* Optional Title input when expanded */}
          {isExpanded && (
            <input
              type="text"
              placeholder="Title (optional - auto generated if empty)"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="mb-2.5 w-full bg-transparent text-sm font-semibold text-neutral-900 placeholder:text-neutral-400 focus:outline-hidden"
              disabled={loading}
            />
          )}

          {/* Main Input */}
          {type === 'note' ? (
            <textarea
              ref={(node) => {
                if (localNoteInputRef) (localNoteInputRef as any).current = node;
                if (externalRef) (externalRef as any).current = node;
              }}
              rows={isExpanded ? 3 : 1}
              placeholder={isExpanded ? 'Type or paste your note content here...' : 'Take a note or paste a URL...'}
              value={content}
              onFocus={() => setIsExpanded(true)}
              onChange={(e) => handleContentChange(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
              className="w-full resize-none bg-transparent text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-hidden leading-relaxed"
            />
          ) : (
            <div className="flex items-center gap-2">
              <Globe className="h-4 w-4 text-neutral-400 shrink-0" />
              <input
                ref={(node) => {
                  if (localUrlInputRef) (localUrlInputRef as any).current = node;
                  if (externalRef && type === 'url') (externalRef as any).current = node;
                }}
                type="url"
                placeholder="https://example.com/article"
                value={url}
                onFocus={() => setIsExpanded(true)}
                onChange={(e) => setUrl(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={loading}
                className="w-full bg-transparent text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-hidden"
              />
            </div>
          )}

          {/* Expanded Tags & Submit Section */}
          {isExpanded && (
            <div className="mt-3.5 pt-3 border-t border-neutral-100 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              {/* Tags Section */}
              <div className="flex flex-wrap items-center gap-1.5">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 rounded-md bg-neutral-100 px-2 py-0.5 text-xs text-neutral-700 font-medium"
                  >
                    #{tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="hover:text-neutral-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
                <div className="flex items-center gap-1">
                  <Tag className="h-3 w-3 text-neutral-400" />
                  <input
                    type="text"
                    placeholder="Add tag..."
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ',') {
                        e.preventDefault();
                        handleAddTag();
                      }
                    }}
                    onBlur={handleAddTag}
                    className="w-20 bg-transparent text-xs text-neutral-800 placeholder:text-neutral-400 focus:outline-hidden focus:w-28 transition-all"
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsExpanded(false);
                    setContent('');
                    setUrl('');
                    setTitle('');
                    setTags([]);
                  }}
                  disabled={loading}
                  className="rounded-lg px-3 py-1.5 text-xs font-medium text-neutral-500 hover:bg-neutral-100 hover:text-neutral-900 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleSubmit}
                  disabled={loading || (type === 'note' ? !content.trim() : !url.trim())}
                  className="flex items-center gap-1.5 rounded-lg bg-neutral-900 px-4 py-1.5 text-xs font-medium text-white shadow-xs hover:bg-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      <span>{type === 'url' ? 'Scraping & Indexing...' : 'Chunking & Saving...'}</span>
                    </>
                  ) : (
                    <>
                      <span>Save & Ingest</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Status notification toast */}
      {statusMessage && (
        <div
          className={`mt-2 flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs transition-all ${
            statusMessage.isError
              ? 'bg-red-50 text-red-700 border border-red-200'
              : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
          }`}
        >
          {statusMessage.isError ? (
            <AlertCircle className="h-4 w-4 shrink-0 text-red-500" />
          ) : (
            <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600" />
          )}
          <span className="font-medium">{statusMessage.text}</span>
        </div>
      )}
    </div>
  );
};
