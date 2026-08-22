import React from 'react';
import { Search, RotateCw, Filter, FileText, Globe } from 'lucide-react';
import { ItemType } from '../types';

interface FilterBarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  selectedType: ItemType | undefined;
  onTypeChange: (type: ItemType | undefined) => void;
  selectedTag: string | undefined;
  onTagChange: (tag: string | undefined) => void;
  allTags: string[];
  totalCount: number;
  onRefresh: () => void;
  isLoading: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  searchQuery,
  onSearchChange,
  selectedType,
  onTypeChange,
  selectedTag,
  onTagChange,
  allTags,
  totalCount,
  onRefresh,
  isLoading,
}) => {
  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-2 sm:px-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            placeholder="Search saved notes and URLs..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full rounded-xl border border-neutral-200 bg-white py-2 pl-9 pr-4 text-xs text-neutral-900 placeholder:text-neutral-400 shadow-2xs focus:border-neutral-900 focus:outline-hidden transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-neutral-400 hover:text-neutral-700"
            >
              Clear
            </button>
          )}
        </div>

        {/* Filter Pills & Refresh */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Type Filter Pills */}
          <div className="flex rounded-lg border border-neutral-200 bg-white p-0.5 shadow-2xs">
            <button
              onClick={() => onTypeChange(undefined)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                selectedType === undefined
                  ? 'bg-neutral-900 text-white'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              All ({totalCount})
            </button>
            <button
              onClick={() => onTypeChange('note')}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                selectedType === 'note'
                  ? 'bg-neutral-900 text-white'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              <FileText className="h-3 w-3" />
              <span>Notes</span>
            </button>
            <button
              onClick={() => onTypeChange('url')}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                selectedType === 'url'
                  ? 'bg-neutral-900 text-white'
                  : 'text-neutral-600 hover:text-neutral-900'
              }`}
            >
              <Globe className="h-3 w-3" />
              <span>URLs</span>
            </button>
          </div>

          {/* Tags Dropdown/Pills */}
          {allTags.length > 0 && (
            <div className="hidden md:flex items-center gap-1 overflow-x-auto py-1">
              <span className="text-[11px] text-neutral-400 flex items-center gap-0.5">
                <Filter className="h-3 w-3" />
              </span>
              {allTags.slice(0, 5).map((t) => (
                <button
                  key={t}
                  onClick={() => onTagChange(selectedTag === t ? undefined : t)}
                  className={`rounded-full px-2.5 py-0.5 text-[11px] font-medium transition-all ${
                    selectedTag === t
                      ? 'bg-neutral-900 text-white'
                      : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200 border border-neutral-200'
                  }`}
                >
                  #{t}
                </button>
              ))}
              {selectedTag && !allTags.slice(0, 5).includes(selectedTag) && (
                <button
                  onClick={() => onTagChange(undefined)}
                  className="rounded-full bg-neutral-900 text-white px-2.5 py-0.5 text-[11px] font-medium"
                >
                  #{selectedTag} ✕
                </button>
              )}
            </div>
          )}

          {/* Refresh Button */}
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="rounded-lg border border-neutral-200 bg-white p-2 text-neutral-600 shadow-2xs hover:bg-neutral-50 hover:text-neutral-900 transition-colors"
            title="Refresh Knowledge Inbox"
          >
            <RotateCw className={`h-3.5 w-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  );
};
