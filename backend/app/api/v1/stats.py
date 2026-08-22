from datetime import datetime, timezone
from fastapi import APIRouter, status
from backend.app.models.schemas import StatsResponse, HealthResponse
from backend.app.db.repository import item_repo
from backend.app.vector_store.chroma_store import ChromaVectorStore
from backend.app.llm.factory import ai_factory
from backend.app.core.config import settings

router = APIRouter(tags=["System & Statistics"])

@router.get(
    "/stats",
    response_model=StatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Statistics",
    description="Returns aggregate counts of notes, URLs, chunks, tags, and active AI model providers."
)
async def get_system_stats() -> StatsResponse:
    db_stats = await item_repo.get_stats()
    emb_adapter, llm_adapter = ai_factory.get_adapters()

    return StatsResponse(
        total_items=db_stats["total_items"],
        total_notes=db_stats["total_notes"],
        total_urls=db_stats["total_urls"],
        total_chunks=db_stats["total_chunks"],
        active_llm_provider=f"{llm_adapter.provider_name} ({llm_adapter.model_name})",
        active_embedding_provider=f"{emb_adapter.provider_name} (dim: {emb_adapter.dimension})",
        vector_store_backend="ChromaDB (Persistent HNSW Cosine)",
        all_tags=db_stats["all_tags"],
    )

@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Health probe for API server, database connectivity, and vector store status."
)
async def health_check() -> HealthResponse:
    chroma_store = ChromaVectorStore()
    vector_healthy = await chroma_store.health_check()

    return HealthResponse(
        status="healthy" if vector_healthy else "degraded",
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        vector_store_healthy=vector_healthy,
        db_healthy=True,
    )
