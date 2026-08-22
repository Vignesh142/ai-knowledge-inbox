import os
import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import Any, Dict, List, Optional, Tuple
from backend.app.vector_store.base import BaseVectorStore
from backend.app.core.config import settings
from backend.app.core.logging import logger

class ChromaVectorStore(BaseVectorStore):
    """
    Production vector store using persistent ChromaDB with automatic
    dimension detection, multi-provider collection partitioning, and recovery.
    """

    def __init__(self, persist_dir: str = settings.CHROMA_PERSIST_DIR):
        self.persist_dir = persist_dir
        os.makedirs(self.persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name_base = "inbox_chunks"

    def _get_or_create_collection_for_dim(self, dim: int):
        """Namespace collections by vector dimension (e.g. inbox_chunks_3072, inbox_chunks_384)."""
        coll_name = f"{self.collection_name_base}_d{dim}"
        return self.client.get_or_create_collection(
            name=coll_name,
            metadata={"hnsw:space": "cosine"}
        )

    def _get_primary_collection(self):
        """Retrieve most recently active collection or default."""
        try:
            colls = self.client.list_collections()
            if colls:
                # Find collection with largest count
                sorted_colls = sorted(colls, key=lambda c: c.count(), reverse=True)
                return sorted_colls[0]
        except Exception:
            pass
        return self.client.get_or_create_collection(
            name=f"{self.collection_name_base}_default",
            metadata={"hnsw:space": "cosine"}
        )

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        clean = {}
        for k, v in metadata.items():
            if isinstance(v, (int, float, str, bool)):
                clean[k] = v
            elif isinstance(v, (list, tuple)):
                clean[k] = ", ".join(str(item) for item in v)
            elif v is None:
                clean[k] = ""
            else:
                clean[k] = str(v)
        return clean

    async def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if not chunk_ids or not embeddings:
            return
        
        dim = len(embeddings[0])
        collection = self._get_or_create_collection_for_dim(dim)
        clean_metas = [self._sanitize_metadata(m) for m in metadatas]
        
        collection.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=clean_metas,
        )
        logger.info(f"Upserted {len(chunk_ids)} chunk vectors to ChromaDB (dim: {dim}). Total: {collection.count()}")

    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, str, Dict[str, Any], float]]:
        dim = len(query_embedding)
        collection = self._get_or_create_collection_for_dim(dim)
        
        total_in_coll = collection.count()
        if total_in_coll == 0:
            logger.info(f"Chroma collection for dim {dim} is currently empty.")
            return []

        actual_k = min(top_k, total_in_coll)
        where_clause = None
        if filters:
            conditions = []
            for k, v in filters.items():
                if v is not None:
                    conditions.append({k: {"$eq": v}})
            if len(conditions) == 1:
                where_clause = conditions[0]
            elif len(conditions) > 1:
                where_clause = {"$and": conditions}

        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=actual_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Chroma similarity search error: {e}")
            return []

        matches: List[Tuple[str, str, Dict[str, Any], float]] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return matches

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else [""] * len(ids)
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(ids)

        for cid, doc, meta, dist in zip(ids, docs, metas, distances):
            similarity = max(0.0, min(1.0, 1.0 - float(dist)))
            matches.append((cid, doc, meta, round(similarity, 4)))

        matches.sort(key=lambda x: x[3], reverse=True)
        return matches

    async def delete_by_item_id(self, item_id: str) -> None:
        try:
            for coll in self.client.list_collections():
                try:
                    coll.delete(where={"item_id": item_id})
                except Exception:
                    pass
            logger.info(f"Deleted vector chunks across collections for item_id: {item_id}")
        except Exception as e:
            logger.warning(f"Error deleting chunks for item_id {item_id}: {e}")

    async def count(self) -> int:
        total = 0
        try:
            for coll in self.client.list_collections():
                total += coll.count()
        except Exception:
            pass
        return total

    async def health_check(self) -> bool:
        try:
            _ = self.client.list_collections()
            return True
        except Exception:
            return False
