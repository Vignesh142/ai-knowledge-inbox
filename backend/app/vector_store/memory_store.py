import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from backend.app.vector_store.base import BaseVectorStore
from backend.app.core.logging import logger

class MemoryVectorStore(BaseVectorStore):
    """In-memory vector store using numpy cosine similarity."""

    def __init__(self):
        self.chunk_ids: List[str] = []
        self.embeddings: List[np.ndarray] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []

    async def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        for cid, emb, doc, meta in zip(chunk_ids, embeddings, documents, metadatas):
            # If already exists, replace
            if cid in self.chunk_ids:
                idx = self.chunk_ids.index(cid)
                self.embeddings[idx] = np.array(emb, dtype=np.float32)
                self.documents[idx] = doc
                self.metadatas[idx] = meta
            else:
                self.chunk_ids.append(cid)
                self.embeddings.append(np.array(emb, dtype=np.float32))
                self.documents.append(doc)
                self.metadatas.append(meta)
        logger.info(f"In-memory store now holds {len(self.chunk_ids)} chunks.")

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, str, Dict[str, Any], float]]:
        if not self.chunk_ids:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        scores: List[Tuple[str, str, Dict[str, Any], float]] = []

        for cid, emb, doc, meta in zip(self.chunk_ids, self.embeddings, self.documents, self.metadatas):
            if filters:
                match = True
                for k, v in filters.items():
                    if meta.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            emb_norm = np.linalg.norm(emb)
            if emb_norm == 0:
                similarity = 0.0
            else:
                similarity = float(np.dot(q_vec, emb / emb_norm))

            # Clamp between 0.0 and 1.0
            similarity = max(0.0, min(1.0, (similarity + 1.0) / 2.0 if similarity < 0 else similarity))
            scores.append((cid, doc, meta, round(similarity, 4)))

        scores.sort(key=lambda x: x[3], reverse=True)
        return scores[:top_k]

    async def delete_by_item_id(self, item_id: str) -> None:
        keep_indices = [i for i, meta in enumerate(self.metadatas) if meta.get("item_id") != item_id]
        self.chunk_ids = [self.chunk_ids[i] for i in keep_indices]
        self.embeddings = [self.embeddings[i] for i in keep_indices]
        self.documents = [self.documents[i] for i in keep_indices]
        self.metadatas = [self.metadatas[i] for i in keep_indices]

    async def count(self) -> int:
        return len(self.chunk_ids)

    async def health_check(self) -> bool:
        return True
