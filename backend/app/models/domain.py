import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

class ItemType(str, Enum):
    NOTE = "note"
    URL = "url"

def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ChunkRecord(BaseModel):
    """Pydantic model representing a semantic chunk entity in the database."""
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    chunk_index: int = 0
    text: str
    char_count: int = 0
    token_estimate: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_row(cls, row: Any) -> "ChunkRecord":
        raw_meta = row["metadata"] if "metadata" in row.keys() else "{}"
        if isinstance(raw_meta, str):
            try:
                parsed_meta = json.loads(raw_meta)
            except Exception:
                parsed_meta = {}
        else:
            parsed_meta = raw_meta or {}

        return cls(
            id=row["id"],
            item_id=row["item_id"],
            chunk_index=row["chunk_index"],
            text=row["text"],
            char_count=row["char_count"],
            token_estimate=row["token_estimate"],
            metadata=parsed_meta,
        )

    def to_db_tuple(self) -> tuple:
        return (
            self.id,
            self.item_id,
            self.chunk_index,
            self.text,
            self.char_count,
            self.token_estimate,
            json.dumps(self.metadata),
        )

class ItemRecord(BaseModel):
    """Pydantic model representing an ingested item (note or URL) in the database."""
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ItemType = ItemType.NOTE
    title: str = ""
    content: str = ""
    url: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    chunk_count: int = 0
    created_at: datetime = Field(default_factory=get_utc_now)
    updated_at: datetime = Field(default_factory=get_utc_now)

    @classmethod
    def from_row(cls, row: Any) -> "ItemRecord":
        raw_meta = row["source_metadata"] if "source_metadata" in row.keys() else "{}"
        if isinstance(raw_meta, str):
            try:
                parsed_meta = json.loads(raw_meta)
            except Exception:
                parsed_meta = {}
        else:
            parsed_meta = raw_meta or {}

        raw_tags = row["tags"] if "tags" in row.keys() else "[]"
        if isinstance(raw_tags, str):
            try:
                parsed_tags = json.loads(raw_tags)
            except Exception:
                parsed_tags = []
        else:
            parsed_tags = raw_tags or []

        created = row["created_at"]
        if isinstance(created, str):
            created_dt = datetime.fromisoformat(created)
        else:
            created_dt = created

        updated = row["updated_at"]
        if isinstance(updated, str):
            updated_dt = datetime.fromisoformat(updated)
        else:
            updated_dt = updated

        return cls(
            id=row["id"],
            type=ItemType(row["type"]),
            title=row["title"],
            content=row["content"],
            url=row["url"],
            source_metadata=parsed_meta,
            tags=parsed_tags,
            chunk_count=row["chunk_count"],
            created_at=created_dt,
            updated_at=updated_dt,
        )

    def to_db_tuple(self) -> tuple:
        return (
            self.id,
            self.type.value,
            self.title,
            self.content,
            self.url,
            json.dumps(self.source_metadata),
            json.dumps(self.tags),
            self.chunk_count,
            self.created_at.isoformat(),
            self.updated_at.isoformat(),
        )

class SourceCitation(BaseModel):
    """Pydantic model representing a cited source chunk."""
    model_config = ConfigDict(from_attributes=True)

    chunk_id: str
    item_id: str
    item_title: str
    item_type: str
    url: Optional[str] = None
    snippet: str
    similarity_score: float
    chunk_index: int

Item = ItemRecord
Chunk = ChunkRecord
