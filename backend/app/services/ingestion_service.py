import uuid
from datetime import datetime, timezone
from typing import Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.domain import ItemRecord, ItemType, ChunkRecord
from backend.app.models.schemas import IngestRequest
from backend.app.db.repository import item_repo, ItemRepository
from backend.app.vector_store.base import BaseVectorStore
from backend.app.vector_store.chroma_store import ChromaVectorStore
from backend.app.llm.base import BaseEmbeddingAdapter
from backend.app.llm.factory import ai_factory
from backend.app.services.scraper_service import scraper_service, ScraperService
from backend.app.services.chunker_service import chunker_service, ChunkerService

class IngestionService:
    """Orchestrates end-to-end ingestion pipeline: scrape/validate -> chunk -> embed -> store."""

    def __init__(
        self,
        repo: ItemRepository = item_repo,
        vector_store: Optional[BaseVectorStore] = None,
        embedding_adapter: Optional[BaseEmbeddingAdapter] = None,
        scraper: ScraperService = scraper_service,
        chunker: ChunkerService = chunker_service,
    ):
        self.repo = repo
        self.vector_store = vector_store or ChromaVectorStore()
        self.embedding_adapter = embedding_adapter or ai_factory.get_embedding_adapter()
        self.scraper = scraper
        self.chunker = chunker

    async def sync_all_chunks_to_vector_store(self) -> int:
        """
        Synchronizes all SQLite chunks into the active vector store collection.
        Ensures smooth transitions when changing embedding providers/dimensions.
        """
        try:
            items, total = await self.repo.list_items(size=500)
            if not items:
                return 0

            synced_count = 0
            for item in items:
                result = await self.repo.get_with_chunks(item.id)
                if not result:
                    continue
                _, chunks = result
                if not chunks:
                    continue

                texts = [c.text for c in chunks]
                embeddings = await self.embedding_adapter.embed_texts(texts)
                chunk_ids = [c.id for c in chunks]
                documents = [c.text for c in chunks]
                metadatas = [c.metadata for c in chunks]

                await self.vector_store.add_chunks(
                    chunk_ids=chunk_ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )
                synced_count += len(chunks)

            logger.info(f"Synchronized {synced_count} chunks into active vector collection.")
            return synced_count
        except Exception as e:
            logger.warning(f"Error during vector sync on startup: {e}")
            return 0

    async def ingest(self, request: IngestRequest) -> ItemRecord:
        item_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        if request.type == "url":
            scraped_title, content, source_metadata = await self.scraper.scrape_url(request.url)
            final_title = request.title or scraped_title or f"Page from {source_metadata.get('domain', 'web')}"
            item = ItemRecord(
                id=item_id,
                type=ItemType.URL,
                title=final_title,
                content=content,
                url=request.url,
                source_metadata=source_metadata,
                tags=request.tags,
                chunk_count=0,
                created_at=now,
                updated_at=now,
            )
        else:
            raw_content = (request.content or "").strip()
            first_line = raw_content.split("\n")[0].strip()
            inferred_title = (first_line[:60] + "...") if len(first_line) > 60 else (first_line or "Untitled Note")
            final_title = request.title or inferred_title

            source_metadata = {
                "word_count": len(raw_content.split()),
                "char_count": len(raw_content),
            }

            item = ItemRecord(
                id=item_id,
                type=ItemType.NOTE,
                title=final_title,
                content=raw_content,
                url=None,
                source_metadata=source_metadata,
                tags=request.tags,
                chunk_count=0,
                created_at=now,
                updated_at=now,
            )

        # 1. Chunk document
        chunks = self.chunker.chunk_item(item)
        if not chunks:
            chunks = [
                ChunkRecord(
                    id=str(uuid.uuid4()),
                    item_id=item.id,
                    chunk_index=0,
                    text=item.content or item.title,
                    char_count=len(item.content or item.title),
                    token_estimate=max(1, len(item.content or item.title) // 4),
                    metadata={"item_id": item.id, "title": item.title, "type": item.type.value},
                )
            ]

        # 2. Generate vector embeddings in batch
        texts_to_embed = [c.text for c in chunks]
        embeddings = await self.embedding_adapter.embed_texts(texts_to_embed)

        # 3. Store raw item & chunks in SQLite
        persisted_item = await self.repo.create_item_with_chunks(item, chunks)

        # 4. Store vectors in ChromaDB
        chunk_ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [c.metadata for c in chunks]

        await self.vector_store.add_chunks(
            chunk_ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(
            f"Successfully ingested {item.type.value} '{item.title}' (ID: {item.id}) "
            f"with {len(chunks)} chunks and vectors."
        )
        return persisted_item

    async def delete_item(self, item_id: str) -> bool:
        await self.vector_store.delete_by_item_id(item_id)
        deleted = await self.repo.delete_item(item_id)
        return deleted

ingestion_service = IngestionService()
