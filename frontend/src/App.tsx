import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from './components/Header';
import { IngestBar } from './components/IngestBar';
import { FilterBar } from './components/FilterBar';
import { ItemsGrid } from './components/ItemsGrid';
import { ItemDetailModal } from './components/ItemDetailModal';
import { AIChatDrawer } from './components/AIChatDrawer';
import { StatsModal } from './components/StatsModal';
import { Item, ItemType, Stats } from './types';
import { fetchItems, fetchStats, deleteItem } from './services/api';

export const App: React.FC = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Filters state
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedType, setSelectedType] = useState<ItemType | undefined>(undefined);
  const [selectedTag, setSelectedTag] = useState<string | undefined>(undefined);

  // UI Modals & Drawers state
  const [selectedItem, setSelectedItem] = useState<Item | null>(null);
  const [isChatOpen, setIsChatOpen] = useState<boolean>(false);
  const [isStatsOpen, setIsStatsOpen] = useState<boolean>(false);
  const [chatInitialQuery, setChatInitialQuery] = useState<string>('');

  const ingestInputRef = useRef<HTMLTextAreaElement | HTMLInputElement | null>(null);

  // Load items
  const loadItems = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchItems({
        q: searchQuery || undefined,
        type: selectedType,
        tag: selectedTag,
        size: 50,
      });
      setItems(data.items);
      setTotalCount(data.total);
    } catch (err) {
      console.error('Failed to load items:', err);
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, selectedType, selectedTag]);

  // Load stats
  const loadStats = useCallback(async () => {
    try {
      const s = await fetchStats();
      setStats(s);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  useEffect(() => {
    loadItems();
  }, [loadItems]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  // Global Keyboard Shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl/Cmd + K: Toggle AI Chat
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        setIsChatOpen((prev) => !prev);
      }
      // Escape: Close modals / chat
      if (e.key === 'Escape') {
        if (selectedItem) setSelectedItem(null);
        else if (isStatsOpen) setIsStatsOpen(false);
        else if (isChatOpen) setIsChatOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedItem, isStatsOpen, isChatOpen]);

  const handleItemIngested = (newItem: Item) => {
    setItems((prev) => [newItem, ...prev]);
    setTotalCount((prev) => prev + 1);
    loadStats();
  };

  const handleDeleteItem = async (id: string) => {
    try {
      await deleteItem(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
      setTotalCount((prev) => Math.max(0, prev - 1));
      if (selectedItem?.id === id) setSelectedItem(null);
      loadStats();
    } catch (err) {
      alert(`Failed to delete item: ${err}`);
    }
  };

  const handleAskAboutItem = (item: Item) => {
    setChatInitialQuery(`Tell me about "${item.title}" and summarize its key insights.`);
    setIsChatOpen(true);
  };

  const handleViewSourceFromChat = async (itemId: string) => {
    const found = items.find((i) => i.id === itemId);
    if (found) {
      setSelectedItem(found);
    } else {
      try {
        const itemRes = await fetchItems({ q: itemId });
        if (itemRes.items.length > 0) setSelectedItem(itemRes.items[0]);
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleFocusIngest = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => {
      ingestInputRef.current?.focus();
    }, 200);
  };

  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col selection:bg-neutral-900 selection:text-white">
      {/* Top Header */}
      <Header
        stats={stats}
        onOpenStats={() => setIsStatsOpen(true)}
        onToggleChat={() => setIsChatOpen((prev) => !prev)}
        isChatOpen={isChatOpen}
        onFocusIngest={handleFocusIngest}
      />

      {/* Main Container */}
      <main className="flex-1 pb-16">
        {/* Ingest Note & URL Bar (Google Keep inspired) */}
        <IngestBar onItemIngested={handleItemIngested} inputRef={ingestInputRef} />

        {/* Filter and Search Bar */}
        <FilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedType={selectedType}
          onTypeChange={setSelectedType}
          selectedTag={selectedTag}
          onTagChange={setSelectedTag}
          allTags={stats?.all_tags || []}
          totalCount={totalCount}
          onRefresh={() => {
            loadItems();
            loadStats();
          }}
          isLoading={isLoading}
        />

        {/* Saved Content Cards Grid */}
        <ItemsGrid
          items={items}
          isLoading={isLoading}
          onSelectItem={setSelectedItem}
          onDeleteItem={handleDeleteItem}
          onAskAboutItem={handleAskAboutItem}
          onTagClick={(tag) => setSelectedTag(tag)}
          onAddNewClick={handleFocusIngest}
        />
      </main>

      {/* Item Detail & Chunk Inspector Modal */}
      <ItemDetailModal
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
        onDelete={handleDeleteItem}
        onAskAboutItem={handleAskAboutItem}
      />

      {/* AI RAG Query Drawer */}
      <AIChatDrawer
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        onViewSourceItem={handleViewSourceFromChat}
        initialQuery={chatInitialQuery}
      />

      {/* System Diagnostics & Vector DB Stats Modal */}
      <StatsModal
        stats={stats}
        isOpen={isStatsOpen}
        onClose={() => setIsStatsOpen(false)}
      />
    </div>
  );
};

export default App;
