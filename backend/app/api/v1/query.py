from fastapi import APIRouter, status
from fastapi.responses import StreamingResponse
from backend.app.models.schemas import QueryRequest, QueryResponse
from backend.app.services.rag_service import rag_service
from backend.app.core.logging import logger

router = APIRouter(prefix="/query", tags=["RAG Semantic Query"])

@router.post(
    "",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Knowledge Inbox (JSON)",
    description="Performs semantic vector search across your saved notes/URLs, retrieves top chunks, and returns LLM answer with cited sources."
)
async def query_knowledge_inbox(request: QueryRequest) -> QueryResponse:
    logger.info(f"Processing query: '{request.question}' (top_k={request.top_k})")
    response = await rag_service.answer_query(request)
    return response

@router.post(
    "/stream",
    status_code=status.HTTP_200_OK,
    summary="Query Knowledge Inbox (SSE Stream)",
    description="Streams real-time LLM tokens and citations via Server-Sent Events (SSE)."
)
async def stream_query_knowledge_inbox(request: QueryRequest):
    logger.info(f"Processing streaming query: '{request.question}'")
    return StreamingResponse(
        rag_service.stream_query(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
