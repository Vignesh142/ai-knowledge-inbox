import re
import uuid
from typing import Any, Dict, List
from backend.app.core.config import settings
from backend.app.models.domain import ItemRecord, ChunkRecord
from backend.app.core.logging import logger

class ChunkerService:
    """
    Intentional Recursive Character Chunker.
    Splits text hierarchically across paragraphs, lines, sentences, and words
    with sliding window overlap to maintain contextual continuity for vector search.
    """

    def __init__(self, chunk_size: int = settings.CHUNK_SIZE, chunk_overlap: int = settings.CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def _split_text_recursively(self, text: str, max_size: int) -> List[str]:
        if len(text) <= max_size:
            return [text]

        # Splitting hierarchy
        separators = ["\n\n", "\n", ". ", "? ", "! ", " "]
        for sep in separators:
            if sep in text:
                parts = text.split(sep)
                merged_chunks = []
                current = ""

                for p in parts:
                    candidate = f"{current}{sep}{p}" if current else p
                    if len(candidate) <= max_size:
                        current = candidate
                    else:
                        if current:
                            merged_chunks.append(current)
                        if len(p) > max_size:
                            # Recurse on the oversized sub-part with finer separator
                            sub_parts = self._split_text_recursively(p, max_size)
                            merged_chunks.extend(sub_parts)
                            current = ""
                        else:
                            current = p

                if current:
                    merged_chunks.append(current)

                return merged_chunks

        # If no separator found, hard split
        return [text[i:i + max_size] for i in range(0, len(text), max_size)]

    def chunk_text(self, text: str, item_id: str, base_metadata: Dict[str, Any]) -> List[ChunkRecord]:
        if not text or not text.strip():
            return []

        clean_text = text.strip()
        raw_splits = self._split_text_recursively(clean_text, self.chunk_size)

        chunks: List[ChunkRecord] = []
        accumulated_text = ""
        current_chunk_parts = []
        current_length = 0

        for part in raw_splits:
            part = part.strip()
            if not part:
                continue

            if current_length + len(part) + 1 <= self.chunk_size:
                current_chunk_parts.append(part)
                current_length += len(part) + 1
            else:
                if current_chunk_parts:
                    chunk_str = "\n".join(current_chunk_parts)
                    chunk_meta = dict(base_metadata)
                    chunk_meta["chunk_index"] = len(chunks)
                    chunk_meta["item_id"] = item_id

                    chunks.append(
                        ChunkRecord(
                            id=str(uuid.uuid4()),
                            item_id=item_id,
                            chunk_index=len(chunks),
                            text=chunk_str,
                            char_count=len(chunk_str),
                            token_estimate=max(1, len(chunk_str) // 4),
                            metadata=chunk_meta,
                        )
                    )

                    # Compute overlap from the end of the previous chunk
                    if self.chunk_overlap > 0 and len(chunk_str) > self.chunk_overlap:
                        overlap_text = chunk_str[-self.chunk_overlap:].strip()
                        current_chunk_parts = [overlap_text, part]
                        current_length = len(overlap_text) + len(part) + 1
                    else:
                        current_chunk_parts = [part]
                        current_length = len(part)
                else:
                    current_chunk_parts = [part]
                    current_length = len(part)

        if current_chunk_parts:
            chunk_str = "\n".join(current_chunk_parts)
            chunk_meta = dict(base_metadata)
            chunk_meta["chunk_index"] = len(chunks)
            chunk_meta["item_id"] = item_id

            chunks.append(
                ChunkRecord(
                    id=str(uuid.uuid4()),
                    item_id=item_id,
                    chunk_index=len(chunks),
                    text=chunk_str,
                    char_count=len(chunk_str),
                    token_estimate=max(1, len(chunk_str) // 4),
                    metadata=chunk_meta,
                )
            )

        logger.info(f"Chunked document (id={item_id}, len={len(text)}) into {len(chunks)} semantic chunks.")
        return chunks

    def chunk_item(self, item: ItemRecord) -> List[ChunkRecord]:
        base_meta = {
            "item_id": item.id,
            "title": item.title,
            "type": item.type.value,
            "url": item.url or "",
            "tags": ", ".join(item.tags),
            "created_at": item.created_at.isoformat(),
        }
        return self.chunk_text(item.content, item.id, base_meta)

chunker_service = ChunkerService()
