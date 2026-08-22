from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from backend.app.models.schemas import (
    IngestRequest,
    ItemResponse,
    ItemDetailResponse,
    ItemListResponse,
)
from backend.app.models.domain import ItemRecord
from backend.app.services.ingestion_service import ingestion_service
from backend.app.db.repository import item_repo
from backend.app.core.exceptions import ItemNotFoundError
from backend.app.core.logging import logger

router = APIRouter(prefix="/items", tags=["Knowledge Items"])

def _to_item_response(item: ItemRecord) -> ItemResponse:
    preview = item.content[:240] + ("..." if len(item.content) > 240 else "")
    return ItemResponse(
        id=item.id,
        type=item.type.value,
        title=item.title,
        content_preview=preview,
        url=item.url,
        source_metadata=item.source_metadata,
        tags=item.tags,
        chunk_count=item.chunk_count,
        char_count=len(item.content),
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
    )

@router.post(
    "/ingest",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a Note or URL",
    description="Ingests plain text notes or fetches URLs server-side, chunks the document, embeds it, and stores in vector index."
)
async def ingest_item(request: IngestRequest) -> ItemResponse:
    logger.info(f"Received ingestion request for type='{request.type}'")
    item = await ingestion_service.ingest(request)
    return _to_item_response(item)

@router.get(
    "",
    response_model=ItemListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Saved Items",
    description="Fetch saved knowledge items with pagination, text search, and filtering by type or tag."
)
async def list_items(
    q: Optional[str] = Query(None, description="Search query string"),
    type: Optional[str] = Query(None, description="Filter by 'note' or 'url'"),
    tag: Optional[str] = Query(None, description="Filter by tag name"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
) -> ItemListResponse:
    items, total = await item_repo.list_items(
        search_query=q,
        item_type=type,
        tag=tag,
        page=page,
        size=size,
    )
    return ItemListResponse(
        items=[_to_item_response(it) for it in items],
        total=total,
        page=page,
        size=size,
    )

@router.get(
    "/{item_id}",
    response_model=ItemDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Item Details & Chunks",
    description="Retrieve full content and generated chunks for a specific item."
)
async def get_item(item_id: str) -> ItemDetailResponse:
    result = await item_repo.get_with_chunks(item_id)
    if not result:
        raise ItemNotFoundError(item_id)

    item, chunks = result
    chunks_data = [
        {
            "id": c.id,
            "chunk_index": c.chunk_index,
            "text": c.text,
            "char_count": c.char_count,
            "token_estimate": c.token_estimate,
            "metadata": c.metadata,
        }
        for c in chunks
    ]

    return ItemDetailResponse(
        id=item.id,
        type=item.type.value,
        title=item.title,
        content=item.content,
        url=item.url,
        source_metadata=item.source_metadata,
        tags=item.tags,
        chunk_count=item.chunk_count,
        created_at=item.created_at.isoformat(),
        updated_at=item.updated_at.isoformat(),
        chunks=chunks_data,
    )

@router.delete(
    "/{item_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Saved Item",
    description="Deletes an item from SQLite and removes its chunks from the ChromaDB vector index."
)
async def delete_item(item_id: str):
    deleted = await ingestion_service.delete_item(item_id)
    if not deleted:
        raise ItemNotFoundError(item_id)
    return {"status": "success", "message": f"Item '{item_id}' successfully deleted.", "item_id": item_id}
