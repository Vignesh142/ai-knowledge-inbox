from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class IngestRequest(BaseModel):
    type: Literal["note", "url"] = Field(
        ...,
        description="Type of item to ingest ('note' for plain text or 'url' for web pages)",
        json_schema_extra={"example": "note"}
    )
    content: Optional[str] = Field(
        None,
        description="Plain text content (required if type is 'note')",
        json_schema_extra={"example": "Quick summary of RAG architecture: Retrieval, Augmentation, Generation."}
    )
    url: Optional[str] = Field(
        None,
        description="Web URL to fetch and ingest server-side (required if type is 'url')",
        json_schema_extra={"example": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation"}
    )
    title: Optional[str] = Field(
        None,
        description="Optional custom title (if omitted, auto-generated from content or webpage title)"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Optional tags for organizing knowledge items",
        json_schema_extra={"example": ["ai", "architecture"]}
    )

    @model_validator(mode="after")
    def validate_content_or_url(self):
        if self.type == "note":
            if not self.content or not self.content.strip():
                raise ValueError("Field 'content' is required and cannot be empty when type is 'note'.")
        elif self.type == "url":
            if not self.url or not self.url.strip():
                raise ValueError("Field 'url' is required and cannot be empty when type is 'url'.")
        return self

class SourceCitationSchema(BaseModel):
    chunk_id: str
    item_id: str
    item_title: str
    item_type: str
    url: Optional[str] = None
    snippet: str
    similarity_score: float
    chunk_index: int

class ItemResponse(BaseModel):
    id: str
    type: str
    title: str
    content_preview: str
    url: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    chunk_count: int
    char_count: int
    created_at: str
    updated_at: str

class ItemDetailResponse(BaseModel):
    id: str
    type: str
    title: str
    content: str
    url: Optional[str] = None
    source_metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    chunk_count: int
    created_at: str
    updated_at: str
    chunks: Optional[List[Dict[str, Any]]] = None

class ItemListResponse(BaseModel):
    items: List[ItemResponse]
    total: int
    page: int
    size: int

class QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        description="The question or prompt to search across your knowledge inbox",
        json_schema_extra={"example": "What are the key components of RAG?"}
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant chunks to retrieve for RAG synthesis"
    )
    item_type_filter: Optional[Literal["note", "url"]] = Field(
        None,
        description="Filter retrieval by item type"
    )
    tags_filter: Optional[List[str]] = Field(
        None,
        description="Filter retrieval by tags"
    )

class QueryResponse(BaseModel):
    answer: str
    question: str
    citations: List[SourceCitationSchema]
    retrieval_count: int
    latency_ms: float
    provider_used: str
    model_used: str

class StatsResponse(BaseModel):
    total_items: int
    total_notes: int
    total_urls: int
    total_chunks: int
    active_llm_provider: str
    active_embedding_provider: str
    vector_store_backend: str
    all_tags: List[str]

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    vector_store_healthy: bool
    db_healthy: bool
