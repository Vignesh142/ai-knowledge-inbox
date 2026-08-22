import React from 'react';
import { Item } from '../types';
import { ItemCard } from './ItemCard';
import { Inbox, Sparkles, Plus } from 'lucide-react';

interface ItemsGridProps {
  items: Item[];
  isLoading: boolean;
  onSelectItem: (item: Item) => void;
  onDeleteItem: (id: string) => void;
  onAskAboutItem: (item: Item) => void;
  onTagClick?: (tag: string) => void;
  onAddNewClick?: () => void;
}

export const ItemsGrid: React.FC<ItemsGridProps> = ({
  items,
  isLoading,
  onSelectItem,
  onDeleteItem,
  onAskAboutItem,
  onTagClick,
  onAddNewClick,
}) => {
  if (isLoading && items.length === 0) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="h-44 animate-pulse rounded-xl border border-neutral-200 bg-neutral-100/60 p-4"
            />
          ))}
        </div>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="mx-auto flex w-full max-w-md flex-col items-center justify-center px-4 py-16 text-center">
        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-neutral-100 text-neutral-400 mb-4 border border-neutral-200">
          <Inbox className="h-7 w-7" />
        </div>
        <h3 className="text-base font-semibold text-neutral-900">Your Knowledge Inbox is Empty</h3>
        <p className="mt-1.5 text-xs text-neutral-500 max-w-sm leading-relaxed">
          Capture quick notes, bookmarks, or web articles above. They will be automatically split into semantic chunks and indexed for instant AI Question-Answering.
        </p>
        <button
          onClick={onAddNewClick}
          className="mt-5 flex items-center gap-1.5 rounded-lg bg-neutral-900 px-4 py-2 text-xs font-medium text-white shadow-xs hover:bg-neutral-800 transition-all"
        >
          <Plus className="h-4 w-4" />
          <span>Add First Note or URL</span>
        </button>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-4 sm:px-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {items.map((item) => (
          <ItemCard
            key={item.id}
            item={item}
            onSelect={onSelectItem}
            onDelete={onDeleteItem}
            onAskAboutItem={onAskAboutItem}
            onTagClick={onTagClick}
          />
        ))}
      </div>
    </div>
  );
};
