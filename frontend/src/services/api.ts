import {
  Item,
  ItemDetail,
  IngestPayload,
  QueryResponse,
  SourceCitation,
  Stats,
  ItemType,
} from '../types';

const API_BASE = '/api/v1';

export async function fetchItems(params?: {
  q?: string;
  type?: ItemType;
  tag?: string;
  page?: number;
  size?: number;
}): Promise<{ items: Item[]; total: number }> {
  const query = new URLSearchParams();
  if (params?.q) query.append('q', params.q);
  if (params?.type) query.append('type', params.type);
  if (params?.tag) query.append('tag', params.tag);
  if (params?.page) query.append('page', params.page.toString());
  if (params?.size) query.append('size', params.size.toString());

  const res = await fetch(`${API_BASE}/items?${query.toString()}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Failed to fetch items: HTTP ${res.status}`);
  }
  return res.json();
}

export async function getItemDetail(id: string): Promise<ItemDetail> {
  const res = await fetch(`${API_BASE}/items/${id}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Failed to fetch item details: HTTP ${res.status}`);
  }
  return res.json();
}

export async function ingestItem(payload: IngestPayload): Promise<Item> {
  const res = await fetch(`${API_BASE}/items/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Ingestion failed: HTTP ${res.status}`);
  }
  return res.json();
}

export async function deleteItem(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/items/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Failed to delete item: HTTP ${res.status}`);
  }
}

export async function fetchStats(): Promise<Stats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) {
    throw new Error(`Failed to fetch stats: HTTP ${res.status}`);
  }
  return res.json();
}

export async function queryRAG(
  question: string,
  top_k: number = 5,
  item_type_filter?: ItemType
): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, top_k, item_type_filter }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.error?.message || `Query failed: HTTP ${res.status}`);
  }
  return res.json();
}

export async function streamQueryRAG(
  question: string,
  top_k: number = 5,
  callbacks: {
    onSources?: (citations: SourceCitation[]) => void;
    onToken?: (token: string) => void;
    onDone?: (meta: { latency_ms: number; provider: string; model: string }) => void;
    onError?: (err: Error) => void;
  }
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/query/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, top_k }),
    });

    if (!response.ok || !response.body) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err?.error?.message || `Streaming query failed: HTTP ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      let currentEvent = '';

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) {
          currentEvent = '';
          continue;
        }

        if (line.startsWith('event:')) {
          currentEvent = line.substring(6).trim();
        } else if (line.startsWith('data:')) {
          const rawData = line.substring(5).trim();
          if (!rawData) continue;

          try {
            const parsed = JSON.parse(rawData);
            if (currentEvent === 'sources') {
              callbacks.onSources?.(parsed);
            } else if (currentEvent === 'token') {
              callbacks.onToken?.(parsed);
            } else if (currentEvent === 'done') {
              callbacks.onDone?.(parsed);
            }
          } catch (e) {
            console.error('Failed to parse SSE line data:', rawData, e);
          }
        }
      }
    }
  } catch (err: any) {
    callbacks.onError?.(err instanceof Error ? err : new Error(String(err)));
  }
}
