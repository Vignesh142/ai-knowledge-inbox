import json
from typing import Any, Dict, List, Optional, Tuple
from backend.app.db.database import db
from backend.app.models.domain import ItemRecord, ChunkRecord
from backend.app.core.logging import logger

class ItemRepository:
    """Async repository layer utilizing Pydantic ItemRecord and ChunkRecord for database persistence."""

    async def create_item_with_chunks(self, item: ItemRecord, chunks: List[ChunkRecord]) -> ItemRecord:
        item.chunk_count = len(chunks)
        async with db.get_connection() as conn:
            # Insert item using Pydantic serialization
            await conn.execute(
                """
                INSERT INTO items (id, type, title, content, url, source_metadata, tags, chunk_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                item.to_db_tuple(),
            )

            # Insert chunks in batch
            for chunk in chunks:
                await conn.execute(
                    """
                    INSERT INTO chunks (id, item_id, chunk_index, text, char_count, token_estimate, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    chunk.to_db_tuple(),
                )

            await conn.commit()
            logger.info(f"Persisted Pydantic ItemRecord {item.id} with {len(chunks)} ChunkRecords to SQLite.")
            return item

    async def get_by_id(self, item_id: str) -> Optional[ItemRecord]:
        async with db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT * FROM items WHERE id = ?",
                (item_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return ItemRecord.from_row(row)

    async def get_with_chunks(self, item_id: str) -> Optional[Tuple[ItemRecord, List[ChunkRecord]]]:
        async with db.get_connection() as conn:
            cursor = await conn.execute("SELECT * FROM items WHERE id = ?", (item_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            item = ItemRecord.from_row(row)

            cursor = await conn.execute(
                "SELECT * FROM chunks WHERE item_id = ? ORDER BY chunk_index ASC",
                (item_id,),
            )
            chunk_rows = await cursor.fetchall()
            chunks = [ChunkRecord.from_row(r) for r in chunk_rows]
            return item, chunks

    async def list_items(
        self,
        search_query: Optional[str] = None,
        item_type: Optional[str] = None,
        tag: Optional[str] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[ItemRecord], int]:
        conditions = []
        params = []

        if item_type:
            conditions.append("type = ?")
            params.append(item_type)

        if search_query and search_query.strip():
            query_param = f"%{search_query.strip()}%"
            conditions.append("(title LIKE ? OR content LIKE ?)")
            params.extend([query_param, query_param])

        if tag and tag.strip():
            tag_param = f'%"{tag.strip()}"%'
            conditions.append("tags LIKE ?")
            params.append(tag_param)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        offset = (page - 1) * size

        async with db.get_connection() as conn:
            # Count query
            count_sql = f"SELECT COUNT(*) as total FROM items{where_clause}"
            cursor = await conn.execute(count_sql, params)
            count_row = await cursor.fetchone()
            total = count_row["total"] if count_row else 0

            # Items query
            items_sql = f"SELECT * FROM items{where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
            query_params = list(params) + [size, offset]
            cursor = await conn.execute(items_sql, query_params)
            rows = await cursor.fetchall()
            items = [ItemRecord.from_row(r) for r in rows]

            return items, total

    async def delete_item(self, item_id: str) -> bool:
        async with db.get_connection() as conn:
            cursor = await conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
            await conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted Pydantic ItemRecord {item_id} from database.")
            return deleted

    async def get_stats(self) -> Dict[str, Any]:
        async with db.get_connection() as conn:
            cursor = await conn.execute(
                """
                SELECT 
                    COUNT(*) as total_items,
                    SUM(CASE WHEN type = 'note' THEN 1 ELSE 0 END) as total_notes,
                    SUM(CASE WHEN type = 'url' THEN 1 ELSE 0 END) as total_urls,
                    SUM(chunk_count) as total_chunks
                FROM items
                """
            )
            row = await cursor.fetchone()
            
            # Fetch all distinct tags
            cursor = await conn.execute("SELECT tags FROM items")
            tag_rows = await cursor.fetchall()
            all_tags = set()
            for tr in tag_rows:
                try:
                    for t in json.loads(tr["tags"] or "[]"):
                        all_tags.add(t)
                except Exception:
                    pass

            return {
                "total_items": row["total_items"] or 0,
                "total_notes": row["total_notes"] or 0,
                "total_urls": row["total_urls"] or 0,
                "total_chunks": row["total_chunks"] or 0,
                "all_tags": sorted(list(all_tags)),
            }

item_repo = ItemRepository()
