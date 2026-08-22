export type ItemType = 'note' | 'url';

export interface SourceMetadata {
  title?: string;
  description?: string;
  author?: string;
  domain?: string;
  favicon?: string;
  word_count?: number;
  char_count?: number;
}

export interface Item {
  id: string;
  type: ItemType;
  title: string;
  content_preview: string;
  url?: string;
  source_metadata: SourceMetadata;
  tags: string[];
  chunk_count: number;
  char_count: number;
  created_at: string;
  updated_at: string;
}

export interface Chunk {
  id: string;
  chunk_index: number;
  text: string;
  char_count: number;
  token_estimate: number;
  metadata: Record<string, any>;
}

export interface ItemDetail extends Item {
  content: string;
  chunks?: Chunk[];
}

export interface SourceCitation {
  chunk_id: string;
  item_id: string;
  item_title: string;
  item_type: ItemType;
  url?: string;
  snippet: string;
  similarity_score: number;
  chunk_index: number;
}

export interface QueryResponse {
  answer: string;
  question: string;
  citations: SourceCitation[];
  retrieval_count: number;
  latency_ms: number;
  provider_used: string;
  model_used: string;
}

export interface Stats {
  total_items: number;
  total_notes: number;
  total_urls: number;
  total_chunks: number;
  active_llm_provider: string;
  active_embedding_provider: string;
  vector_store_backend: string;
  all_tags: string[];
}

export interface IngestPayload {
  type: ItemType;
  content?: string;
  url?: string;
  title?: string;
  tags: string[];
}
