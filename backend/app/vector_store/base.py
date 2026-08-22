from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

class BaseVectorStore(ABC):
    """Abstract interface for vector store implementations."""

    @abstractmethod
    async def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Store chunk embeddings, documents and metadata in the vector index."""
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[str, str, Dict[str, Any], float]]:
        """
        Perform vector similarity search.
        Returns a list of tuples: (chunk_id, document_text, metadata, similarity_score)
        where similarity_score is in [0.0, 1.0] (higher is more similar).
        """
        pass

    @abstractmethod
    async def delete_by_item_id(self, item_id: str) -> None:
        """Delete all vectors and chunks associated with a specific item ID."""
        pass

    @abstractmethod
    async def count(self) -> int:
        """Return the total number of vectors in the store."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if vector store is initialized and healthy."""
        pass
